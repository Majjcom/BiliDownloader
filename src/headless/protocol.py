"""Small, Qt-independent building blocks shared by the CLI and executor."""

import json
import sys
import threading
from dataclasses import dataclass
from typing import Tuple


_output_lock = threading.RLock()


class HeadlessError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Operation:
    name: str
    args: Tuple[str, ...] = ()


def emit(event, **fields):
    """All headless events, including errors, use stdout exclusively."""
    record = {"event": event}
    record.update(fields)
    with _output_lock:
        sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
        sys.stdout.flush()


class DiagnosticWriter:
    """Convert Python warnings/tracebacks into stdout JSON Lines."""

    encoding = "utf-8"
    errors = "strict"

    def __init__(self):
        self._buffer = ""
        self._lock = threading.RLock()

    def write(self, text):
        with self._lock:
            self._buffer += text
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                if line.strip():
                    emit("diagnostic", source="runtime", message=line.rstrip("\r"))
        return len(text)

    def flush(self):
        with self._lock:
            if self._buffer.strip():
                emit("diagnostic", source="runtime", message=self._buffer)
            self._buffer = ""

    def isatty(self):
        return False

    def writable(self):
        return True

    def fileno(self):
        return sys.stdout.fileno()


def boolean(value):
    text = str(value).lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off"):
        return False
    raise HeadlessError("需要布尔值 true 或 false：{}".format(value))


def expected_value(value):
    try:
        return json.loads(value)
    except ValueError:
        return value
