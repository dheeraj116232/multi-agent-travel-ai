'''
# pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python pip install requests streamlit

# install PostgresSql and create database
CREATE DATABASE langgraph_memory;  ( or open pgadmin4 and create database there )
'''
# LangGraph Multi-Agent Travel Booking System with Long-Term Memory

# main.py

import os
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Annotated
import operator

import psycopg
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

try:
    from langchain_groq import ChatGroq
except ModuleNotFoundError:  # allow UI to run without groq dependency
    ChatGroq = None

try:
    from langchain_openai import ChatOpenAI
except ModuleNotFoundError:
    ChatOpenAI = None



from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from core.errors import ProductionExternalAPIError

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM
llm = None
if ChatGroq is not None and GROQ_API_KEY:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
    )
elif ChatOpenAI is not None and OPENAI_API_KEY:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=OPENAI_API_KEY,
    )



# State
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

# Flight Agent
def flight_agent(state: TravelState):
    query = state["user_query"]
    try:
        flight_data = search_flights(query)
    except ProductionExternalAPIError:
        flight_data = "⚠️ Live flight data is currently unavailable. Proceeding with estimated information."
    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Hotel Agent
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    try:
        hotel_results = tavily_search(query)
    except ProductionExternalAPIError:
        hotel_results = "⚠️ No hotel results available. Proceeding without hotel recommendations."
    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Itinerary Agent
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    if llm is None:
        return {
            "itinerary": "⚠️ Itinerary agent unavailable - LLM not configured.",
            "messages": [AIMessage(content="Itinerary agent unavailable")],
            "llm_calls": state.get("llm_calls", 0)
        }

    try:
        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel planner"
            ),
            HumanMessage(content=prompt)
        ])
    except Exception as e:
        response_content = f"⚠️ Failed to generate itinerary. Error: {e}"
        return {
            "itinerary": response_content,
            "messages": [AIMessage(content=response_content)],
            "llm_calls": state.get("llm_calls", 0)
        }

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Final Response Agent
def final_agent(state: TravelState):

    final_prompt = f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    if llm is None:
        return {
            "messages": [AIMessage(content="Final agent unavailable - LLM not configured.")],
            "llm_calls": state.get("llm_calls", 0)
        }

    try:
        response = llm.invoke([
            HumanMessage(content=final_prompt)
        ])
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"⚠️ Final response generation failed: {e}")],
            "llm_calls": state.get("llm_calls", 0)
        }

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


_conn = None
checkpointer = None

def test_and_reconnect():
    """Test database connection and reconnect if needed. Returns True if DB is available."""
    import psycopg
    global _conn, checkpointer, app
    if not DATABASE_URL:
        return False
    try:
        if _conn is None:
            raise psycopg.InterfaceError("No connection")
        with _conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        try:
            if _conn:
                _conn.close()
        except Exception:
            pass
        try:
            _conn = psycopg.connect(DATABASE_URL, autocommit=True)
            checkpointer = PostgresSaver(_conn)
            checkpointer.setup()
            # Always compile without checkpointer for Streamlit (uses session_state instead)
            app = graph.compile()
            return True
        except Exception:
            app = graph.compile()
            return False

# Compile without checkpointer for Streamlit (session state handles persistence)
# This avoids stale connection issues in long-running Streamlit processes
app = graph.compile()



if __name__ == "__main__" and os.getenv("RUN_TRAVEL_CLI") == "1":
    # CLI runner (disabled by default; avoids blocking Streamlit)
    config = {
        "configurable": {
            "thread_id": "user_aarohi"
        }
    }

    user_input = input("Enter travel request: ")



    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)
