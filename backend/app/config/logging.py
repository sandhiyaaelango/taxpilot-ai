import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for application logs."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "props"):
            log_obj.update(record.props)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

class StructuredLogger:
    """Wrapper that provides structured logging methods."""
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(event, extra={"props": kwargs})

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(event, extra={"props": kwargs})

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error(event, extra={"props": kwargs})

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(event, extra={"props": kwargs})

def setup_logging(log_level_str: str = "INFO") -> None:
    level = getattr(logging, log_level_str.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name))
