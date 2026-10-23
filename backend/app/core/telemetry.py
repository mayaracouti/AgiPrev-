"""Process-local counters and JSON logs; never log credentials or request bodies."""

import json
import logging
from collections import Counter
from contextvars import ContextVar
from threading import Lock
from uuid import uuid4

correlation: ContextVar[str] = ContextVar("correlation_id", default="")
logger = logging.getLogger("agipreve.events")
_counters: Counter = Counter()
_lock = Lock()


def event(name: str, **fields) -> None:
    with _lock:
        _counters[name] += 1
    logger.warning(
        json.dumps(
            {"event": name, "correlation_id": correlation.get() or str(uuid4()), **fields},
            default=str,
            sort_keys=True,
        )
    )


def counters() -> dict:
    with _lock:
        return dict(_counters)
