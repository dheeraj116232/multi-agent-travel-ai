# Example free API usage
# - AviationStack

# create api key
# https://aviationstack.com/ 
# pip install requests


import os
import re
from datetime import date, datetime
from typing import Any, Dict, Optional, Tuple

import requests
from dotenv import load_dotenv

from core.errors import (
    APIRateLimitError,
    APITimeoutError,
    EmptyAPIResponseError,
    InvalidAPIKeyError,
    MalformedAPIResponseError,
    NetworkConnectivityError,
    ProductionExternalAPIError,
)
from core.logger import get_app_logger
from core.retry import retry_external_call

load_dotenv()

# Silence unused warning in some linters if query is not used for provider params.
# (Declared inside search_flights; this module-level placeholder must not reference it.)
_query_placeholder = None


API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

logger = get_app_logger("flight_agent_api")


AVIATIONSTACK_URL = "http://api.aviationstack.com/v1/flights"


def _detect_and_raise_from_response(resp: requests.Response, data: Any) -> None:
    status_code = resp.status_code
    raw_snippet = str(data)[:500] if data is not None else ""

    if status_code == 429:
        raise APIRateLimitError(
            "AviationStack rate limit reached",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ API rate limit reached. Please wait a few minutes.",
                "raw_snippet": raw_snippet,
            },
        )

    if status_code in (401, 403):
        raise InvalidAPIKeyError(
            "AviationStack invalid API key or restricted function",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": False,
                "user_message": "⚠️ Flight service authentication failed. Please try again later.",
                "raw_snippet": raw_snippet,
            },
        )

    if status_code < 200 or status_code >= 300:
        raise ProductionExternalAPIError(
            f"AviationStack request failed with status {status_code}",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                "raw_snippet": raw_snippet,
            },
        )

    if data is None:
        raise EmptyAPIResponseError(
            "AviationStack response is empty",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": resp.status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
            },
        )

    if not isinstance(data, dict):
        raise MalformedAPIResponseError(
            "AviationStack response is not a JSON object",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": resp.status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service returned unexpected data. Please try again later.",
            },
        )

    if "data" not in data:
        raise MalformedAPIResponseError(
            "AviationStack response missing 'data' field",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service returned unexpected data. Please try again later.",
                "raw_snippet": str(data)[:300],
            },
        )

    if not data.get("data"):
        return False

    return True


def search_flights(query: str) -> str:
    """
    Returns a formatted flight summary string.
    On failure, raises ProductionExternalAPIError (caller handles fallback).
    """
    if not API_KEY:
        raise InvalidAPIKeyError(
            "AVIATIONSTACK_API_KEY missing",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "retryable": False,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
            },
        )

    params: Dict[str, Any] = {
        "access_key": API_KEY,
        "limit": 5,
    }

    def _call() -> str:
        try:
            resp = requests.get(AVIATIONSTACK_URL, params=params, timeout=10)
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(
                "AviationStack request timed out",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                    "raw_snippet": str(e)[:300],
                },
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkConnectivityError(
                "AviationStack connection error",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                    "raw_snippet": str(e)[:300],
                },
            ) from e
        except requests.exceptions.RequestException as e:
            raise NetworkConnectivityError(
                "AviationStack network request error",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                    "raw_snippet": str(e)[:300],
                },
            ) from e

        # Handle non-JSON failure responses gracefully so the caller can fall back without noisy retries.
        content_type = (resp.headers.get("content-type") or "").lower()
        if resp.status_code >= 400 or "json" not in content_type:
            text = (resp.text or "").strip()
            if text:
                return (
                    "Real-time flight data is currently unavailable due to an upstream service error.\n"
                    f"Upstream response ({resp.status_code}): {text[:500]}"
                )
            return "Real-time flight data is currently unavailable. Please try again later."

        try:
            data = resp.json()
        except ValueError as e:
            raise MalformedAPIResponseError(
                "AviationStack returned invalid JSON",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "status_code": resp.status_code,
                    "retryable": True,
                    "user_message": "⚠️ Flight service returned unexpected data. Please try again later.",
                    "raw_snippet": (resp.text or "")[:300],
                },
            ) from e

        _detect_and_raise_from_response(resp, data)

        origin, destination, departure_date = _extract_query(query) or (
            {"code": "JFK", "city": "New York"},
            {"code": "LHR", "city": "London"},
            _default_departure(),
        )
        flights, total_estimate = _select_realistic_routes(data.get("data", []), origin.get("code", "JFK"), destination.get("code", "LHR"))
        if not flights:
            return _default_flight_fallback(origin, destination, departure_date)
        summary = _format_flight_summary(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            flights=flights,
            total_estimate=total_estimate,
        )
        return summary

    # Retry external call; retry only ProductionExternalAPIError subclasses
    try:
        return retry_external_call(
            lambda: _call(),
            retries=2,
            backoff_seconds=(1, 2),
            retry_on=(
                ProductionExternalAPIError,
                APITimeoutError,
                APIRateLimitError,
                InvalidAPIKeyError,
                NetworkConnectivityError,
                MalformedAPIResponseError,
                EmptyAPIResponseError,
            ),
            provider="aviationstack",
            operation="search_flights",
            agent="flight_agent",
        )
    except ProductionExternalAPIError as e:
        # Log structured error
        logger.error(
            "External API call failed after retries",
            extra={
                "agent": "flight_agent",
                "provider": e.context.provider,
                "operation": e.context.operation,
                "status_code": e.context.status_code,
                "exception_type": type(e).__name__,
                "user_message": e.context.user_message,
                "raw_snippet": e.context.raw_snippet,
            },
        )
        # Re-raise so agent can fallback based on type
        raise
    except Exception as e:
        logger.exception("Unexpected flight_tool error")
        raise ProductionExternalAPIError(
            "Unexpected flight tool failure",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "retryable": False,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                "raw_snippet": str(e)[:300],
            },
        ) from e


_NOISE_WORDS = {
    "flight", "flights", "trip", "travel", "plane", "air", "airport", "airports",
    "from", "to", "towards", "the", "a", "an", "and", "or", "via", "through",
    "departing", "leaving", "arriving", "at", "in", "on", "for", "with", "under",
    "budget", "days", "day", "week", "weeks", "month", "months", "year", "years",
    "plan", "plans", "planning", "complete", "best", "cheap", "cheapest", "luxury",
    "direct", "nonstop", "non-stop", "including", "sightseeing", "hotels", "hotel",
    "lakhs", "lakh", "rs", "rupees", "around", "about", "near",
}


def _strip_noise(text: str) -> str:
    words = text.split()
    cleaned = [w for w in words if w not in _NOISE_WORDS]
    return " ".join(cleaned)


_CITY_ALIASES = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "kolkata": "CCU",
    "hyderabad": "HYD",
    "ahmedabad": "AMD",
    "pune": "PNQ",
    "goa": "GOI",
    "dubai": "DXB",
    "singapore": "SIN",
    "london": "LHR",
    "paris": "CDG",
    "tokyo": "NRT",
    "bali": "DPS",
    "denpasar": "DPS",
    "nyc": "JFK",
    "new york": "JFK",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "sydney": "SYD",
    "melbourne": "MEL",
    "amsterdam": "AMS",
    "toronto": "YYZ",
    "vancouver": "YVR",
    "bangkok": "BKK",
    "kuala lumpur": "KUL",
    "hong kong": "HKG",
}


def _normalize(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return re.sub(r"\s+", " ", value.strip().lower())


def _extract_airport_code(value: Optional[str], fallback: Optional[str] = None) -> Tuple[str, Optional[str]]:
    normalized = _normalize(value)
    if not normalized:
        return (fallback or "JFK", None)

    cleaned = _strip_noise(normalized)
    if not cleaned:
        cleaned = normalized

    token = cleaned
    for prefix in ("from", "to", "departing from", "arriving at"):
        if token.startswith(prefix):
            token = token[len(prefix):].strip(" -:()[]{}|")
            break
    for delim in (" to ", " -> ", " → ", " - ", "–", "—", ":", ",", ";", " and "):
        if delim in token:
            token = token.split(delim)[0].strip()
            break
    token = _strip_noise(token)

    matches = re.findall(r"\b([A-Z]{3})\b", normalized.upper())
    if matches:
        return (matches[0], None)
    alias_key = token.lower()
    iata = _CITY_ALIASES.get(alias_key)
    if not iata:
        compact = alias_key.replace(" ", "")
        for key, code in _CITY_ALIASES.items():
            if key.replace(" ", "") == compact:
                iata = code
                break
        else:
            words = alias_key.split()
            for key, code in _CITY_ALIASES.items():
                if all(word in key for word in words):
                    iata = code
                    break
            else:
                for key, code in _CITY_ALIASES.items():
                    key_words = key.split()
                    if any(word in key_words for word in words):
                        iata = code
                        break
    if iata:
        return (iata, None)
    return (fallback or "JFK", token or None)


_INDEX_TO_MONTH = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _default_departure() -> date:
    try:
        return datetime.now().date()
    except Exception:
        return date(2026, 1, 1)


def _extract_query(query: Optional[str]) -> Optional[Tuple[dict, dict, date]]:
    normalized = _normalize(query) or ""
    date_obj = _default_departure()
    match = re.search(
        r"((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?|\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)",
        normalized,
    )
    if match:
        raw = match.group(1)
        for fmt in ("%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
            try:
                date_obj = datetime.strptime(raw, fmt).date()
                break
            except ValueError:
                continue
    if " to " in normalized:
        source, dest = normalized.split(" to ", 1)
    elif " -> " in normalized:
        source, dest = normalized.split(" -> ", 1)
    elif " → " in normalized:
        source, dest = normalized.split(" → ", 1)
    elif " - " in normalized:
        source, dest = normalized.split(" - ", 1)
    else:
        source = dest = None
    if source and dest:
        origin_code, origin_token = _extract_airport_code(source, "DEL")
        destination_code, destination_token = _extract_airport_code(dest, "BOM")
    else:
        origin_code, origin_token = _extract_airport_code(normalized, "DEL")
        destination_code, destination_token = _extract_airport_code(
            _strip_origin_tokens(normalized, origin_code, origin_token),
            origin_code,
        )
    origin = {
        "code": origin_code,
        "city": _city_name(origin_code, origin_token),
    }
    destination = {
        "code": destination_code,
        "city": _city_name(destination_code, destination_token),
    }
    return origin, destination, date_obj


def _strip_origin_tokens(text: str, origin_code: str, origin_token: Optional[str]) -> str:
    cleaned = text
    for token in (
        origin_code.lower(),
        origin_token.lower() if origin_token else None,
        "from",
        "departing",
        "leaving",
        "flights",
        "flight",
        "to",
        "towards",
    ):
        if token:
            cleaned = re.sub(r"\b" + re.escape(token) + r"\b", " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def _city_name(code: str, token: Optional[str]) -> str:
    mapping = {
        "DEL": "Delhi",
        "BOM": "Mumbai",
        "BLR": "Bengaluru",
        "MAA": "Chennai",
        "CCU": "Kolkata",
        "HYD": "Hyderabad",
        "AMD": "Ahmedabad",
        "PNQ": "Pune",
        "GOI": "Goa",
        "DXB": "Dubai",
        "SIN": "Singapore",
        "LHR": "London",
        "CDG": "Paris",
        "NRT": "Tokyo",
        "DPS": "Bali",
        "JFK": "New York",
        "LAX": "Los Angeles",
        "SFO": "San Francisco",
        "SYD": "Sydney",
        "MEL": "Melbourne",
    }
    if token:
        token = token.strip()
        if token:
            return " ".join(word.capitalize() for word in re.split(r"[\s\-_]+", token))
    return mapping.get(code, code)


def _parse_duration(duration: Optional[str]) -> Optional[float]:
    if not duration:
        return None
    duration = duration.strip().lower()
    match = re.search(r"(?:(\d+)h)?\s*(?:(\d+)m)?", duration)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return hours + minutes / 60.0 if hours or minutes else None


def _route_similarity(flight: Dict[str, Any], origin_code: str, destination_code: str) -> float:
    departure_airport = ((flight.get("departure") or {}).get("iata") or "").upper()
    arrival_airport = ((flight.get("arrival") or {}).get("iata") or "").upper()
    departure_city = ((flight.get("departure") or {}).get("airport") or "").lower()
    arrival_city = ((flight.get("arrival") or {}).get("airport") or "").lower()
    origin_city = _city_name(origin_code, None).lower()
    destination_city = _city_name(destination_code, None).lower()
    score = 0.0
    if departure_airport == origin_code:
        score += 4.0
    elif origin_code in departure_airport or origin_city in departure_city:
        score += 2.5
    elif origin_city.split("/")[0] in departure_city:
        score += 1.8
    if arrival_airport == destination_code:
        score += 4.0
    elif destination_code in arrival_airport or destination_city in arrival_city:
        score += 2.5
    elif destination_city.split("/")[0] in arrival_city:
        score += 1.8
    duration_hours = _parse_duration(flight.get("flight_date"))
    if duration_hours and 1 <= duration_hours <= 18:
        score += 1.2
    flight_status = ((flight.get("flight_status") or "")).lower()
    if flight_status in {"active", "scheduled"}:
        score += 0.6
    return score


def _select_realistic_routes(
    data: list, origin_code: str, destination_code: str, top_n: int = 3
) -> Tuple[list, float]:
    if not data:
        return [], 0.0
    ranked = sorted(
        enumerate(data),
        key=lambda item: _route_similarity(item[1], origin_code, destination_code),
        reverse=True,
    )
    selected = []
    seen_codes = set()
    for _, flight in ranked:
        if len(selected) >= top_n:
            break
        dep_code = ((flight.get("departure") or {}).get("iata") or "").upper()
        arr_code = ((flight.get("arrival") or {}).get("iata") or "").upper()
        dep_city = ((flight.get("departure") or {}).get("airport") or "").lower()
        arr_city = ((flight.get("arrival") or {}).get("airport") or "").lower()
        origin_city = _city_name(origin_code, None).lower()
        destination_city = _city_name(destination_code, None).lower()
        is_origin = dep_code == origin_code or origin_city in dep_city
        is_destination = arr_code == destination_code or destination_city in arr_city
        if is_origin and is_destination:
            identifier = f"{dep_code}-{arr_code}"
        elif is_origin:
            identifier = dep_code
        elif is_destination:
            identifier = arr_code
        else:
            identifier = flight.get("flight_date") or flight.get("airline", {}).get("name", "unknown")
        if identifier in seen_codes:
            continue
        seen_codes.add(identifier)
        selected.append(flight)
    if not selected and ranked:
        selected = [flight for _, flight in ranked[:top_n]]
    prices = []
    for flight in selected:
        try:
            prices.append(float((flight.get("flight_price") or 0)))
        except (TypeError, ValueError):
            pass
    estimate = sum(prices[:2]) / 2.0 if prices else 0.0
    return selected, estimate


def _format_flight_summary(
    origin: dict,
    destination: dict,
    departure_date: date,
    flights: list,
    total_estimate: float,
) -> str:
    lines = [
        f"Route: {origin['city']} ({origin['code']}) -> {destination['city']} ({destination['code']})",
        f"Departure Date: {departure_date.strftime('%B %d, %Y')}",
        "",
    ]
    if not flights:
        lines.append("Real-time results are not available right now. Please verify your parameters with the API.")
        return "\n".join(lines)
    for idx, flight in enumerate(flights, 1):
        airline = flight.get("airline", {}).get("name", "Unknown Airline")
        flight_number = flight.get("flight", {}).get("iata") or flight.get("flight_date") or f"Option {idx}"
        dep_info = flight.get("departure", {})
        arr_info = flight.get("arrival", {})
        departure_time = dep_info.get("time") or dep_info.get("scheduled") or "TBD"
        arrival_time = arr_info.get("time") or arr_info.get("scheduled") or "TBD"
        dep_airport = dep_info.get("airport") or origin.get("city", "Origin")
        arr_airport = arr_info.get("airport") or destination.get("city", "Destination")
        dep_code = dep_info.get("iata") or origin.get("code", "")
        arr_code = arr_info.get("iata") or destination.get("code", "")
        status = flight.get("flight_status", "Unknown")
        lines.append(f"Option {idx}: {airline} ({flight_number})")
        lines.append(f"  Time: {departure_time} -> {arrival_time}")
        lines.append(f"  Route: {dep_airport} ({dep_code}) -> {arr_airport} ({arr_code})")
        lines.append(f"  Status: {status.title() if isinstance(status, str) else status}")
    if total_estimate > 0:
        lines.append("")
        lines.append(f"Estimated starting from ~Rs. {round(total_estimate * 83):,} (USD {round(total_estimate, 2)}).")
    lines.append("")
    lines.append("Note: Prices and availability are indicative. Please reconfirm with the live fare before booking.")
    return "\n".join(lines)


def _default_flight_fallback(origin: dict, destination: dict, departure_date: date) -> str:
    return "\n".join([
        f"Route: {origin['city']} ({origin['code']}) -> {destination['city']} ({destination['code']})",
        f"Departure Date: {departure_date.strftime('%B %d, %Y')}",
        "",
        "Real-time flight data is currently unavailable.",
        "Please recheck the airport codes or try again in a few minutes.",
    ])