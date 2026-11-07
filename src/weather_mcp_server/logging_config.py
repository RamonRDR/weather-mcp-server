"""One-line structured operational logs emitted only to stderr."""

import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "event": record.getMessage(),
            },
            ensure_ascii=False,
        )


def configure_logging(level: str) -> logging.Logger:
    logger = logging.getLogger("weather_mcp_server")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger
