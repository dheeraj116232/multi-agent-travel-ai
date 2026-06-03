from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict


def _ensure_log_dir() -> str:
    repo_root = os.path.dirname(os.path.dirname(__file__))
    logs_dir = os.path.join(repo_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach extra fields (if any)
        for k, v in record.__dict__.items():
            if k in {"msg", "args", "levelname", "levelno", "name", "pathname", "filename", "module", "exc_info", "exc_text",
                     "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName",
                     "processName", "process", "message"}:
                continue
            if k.startswith("_"):
                continue
            # allow None
            payload[k] = v

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


_app_logger: logging.Logger | None = None


def get_app_logger(name: str = "app") -> logging.Logger:
    global _app_logger
    if _app_logger is not None:
        return _app_logger

    logs_dir = _ensure_log_dir()
    log_path = os.path.join(logs_dir, "app.log")

    logger = logging.getLogger("structured_app_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Avoid duplicate handlers on reloads
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JsonFormatter())

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(JsonFormatter())

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    _app_logger = logger
    return logger
