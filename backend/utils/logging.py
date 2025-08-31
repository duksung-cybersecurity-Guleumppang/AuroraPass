import structlog
import logging
import sys
import json
from functools import partial
from typing import Any


def configure_logging() -> None:
    """Configure structured logging with JSON output"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(
                serializer=partial(json.dumps, ensure_ascii=False)
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> Any:
    """Get a structured logger instance"""
    return structlog.get_logger(name)
