"""Structured metadata logs without request bodies, raw IPs or exception messages."""

import json
import logging
from datetime import UTC, datetime


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "event": record.getMessage(),
            }
        )
