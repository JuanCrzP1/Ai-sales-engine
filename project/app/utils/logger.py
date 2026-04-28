import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENABLE_FILE_LOGS = str(os.getenv("ENABLE_FILE_LOGS") or "0").strip().lower() in {"1", "true", "yes"}
LOGS_DIR = PROJECT_ROOT / "logs" if ENABLE_FILE_LOGS else None
if ENABLE_FILE_LOGS and LOGS_DIR is not None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_FILE = (LOGS_DIR / "audit.log") if LOGS_DIR is not None else None
APP_LOG_FILE = (LOGS_DIR / "app.log") if LOGS_DIR is not None else None

STANDARD_LOG_KEYS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info",
    "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread",
    "threadName", "processName", "process", "message", "asctime",
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        super().format(record)
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_KEYS:
                continue
            if value is None:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


def configure_logger(name: str = "assistant") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
    )
    stream_handler.setFormatter(stream_formatter)

    logger.addHandler(stream_handler)
    if ENABLE_FILE_LOGS and APP_LOG_FILE is not None:
        file_handler = RotatingFileHandler(APP_LOG_FILE, 'a', 5 * 1024 * 1024, 3, encoding='utf-8', delay=True)
        file_handler.setFormatter(JsonFormatter(datefmt='%Y-%m-%dT%H:%M:%S'))
        logger.addHandler(file_handler)

    return logger


def configure_audit_logger() -> logging.Logger:
    audit_logger = logging.getLogger("assistant-audit")
    if audit_logger.handlers:
        return audit_logger

    if not ENABLE_FILE_LOGS or AUDIT_LOG_FILE is None:
        audit_logger.addHandler(logging.NullHandler())
        return audit_logger

    audit_logger.setLevel(logging.INFO)

    audit_handler = RotatingFileHandler(AUDIT_LOG_FILE, 'a', 10 * 1024 * 1024, 5, encoding='utf-8', delay=True)
    audit_handler.setFormatter(JsonFormatter(datefmt='%Y-%m-%dT%H:%M:%S'))

    audit_logger.addHandler(audit_handler)

    return audit_logger


def alert_on_audit_event(event: str, **metadata):
    audit = configure_audit_logger()
    payload = {
        "event": event,
        "status": "alert-triggered",
        **metadata,
    }
    # Alert mechanism stub (expand to Slack/email/SIEM as required).
    audit.warning("audit_alert", extra=payload)


# Default module loggers
logger = configure_logger()
audit_logger = configure_audit_logger()
