import logging
import logging.config
import os
from typing import Any, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


HTTP_LOGGER_PREFIXES = (
    "httpx",
    "httpcore",
    "urllib3",
    "aiohttp",
    "uvicorn.access",
)

_HTTP_INFO_ENABLED = False


class LoggingSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


def _resolve_log_level() -> int:
    level_name = LoggingSettings().LOG_LEVEL.strip().upper()
    return getattr(logging, level_name, logging.INFO)


def _build_logging_config(log_level: int) -> Dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "http_info_to_debug": {
                "()": HttpInfoToDebugFilter,
            }
        },
        "formatters": {
            "default": {
                "()": ConditionalFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "level": log_level,
                "filters": ["http_info_to_debug"],
            },
        },
        "root": {"handlers": ["console"], "level": log_level},
        "loggers": {
            "gunicorn": {"propagate": True},
            "gunicorn.access": {"propagate": True},
            "gunicorn.error": {"propagate": True},
            "uvicorn": {"propagate": True},
            "uvicorn.access": {"propagate": True},
            "uvicorn.error": {"propagate": True},
        },
    }


class ConditionalFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record into a string, including timestamp, log level, and message.
        For log records with level ERROR or CRITICAL, also appends the source file path and line number.
        Args:
            record (logging.LogRecord): The log record to format.
        Returns:
            str: The formatted log message.
        """
                
        raw_log_type = getattr(record, "log_type", None)
        tag_segment = ""
        if raw_log_type:
            log_type = str(raw_log_type).strip()
            if log_type:
                if log_type.startswith("[") and log_type.endswith("]"):
                    tag_segment = f" | {log_type}"
                else:
                    tag_segment = f" | [{log_type}]"

        # Display pathname + lineno only for ERROR and CRITICAL
        if record.levelno >= logging.ERROR:
            return f"{self.formatTime(record)} | [{record.levelname}] | ({record.pathname}:{record.lineno}){tag_segment} | {record.getMessage()}"
        
        return f"{self.formatTime(record)} | [{record.levelname}]{tag_segment} | {record.getMessage()}"


class HttpInfoToDebugFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if _HTTP_INFO_ENABLED:
            return True

        if record.levelno == logging.INFO and any(
            record.name.startswith(prefix) for prefix in HTTP_LOGGER_PREFIXES
        ):
            return False

        return True

def setup_logging():
    global _HTTP_INFO_ENABLED

    log_level = _resolve_log_level()
    _HTTP_INFO_ENABLED = log_level <= logging.DEBUG

    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(_build_logging_config(log_level))
