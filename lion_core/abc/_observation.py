from abc import abstractmethod
from enum import Enum
from typing import Any, NoReturn

from lion_core.abc._concept import AbstractObservation
from lion_core.exceptions import LionAccessError


class EventStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Event(AbstractObservation):
    """Discrete occurrences or state changes."""

    status: EventStatus

    @property
    def request(self) -> dict:
        """Retrieve the permission request payload."""
        return self._request()

    def _request(self) -> dict:
        """override this method in child class."""
        return {}

    @classmethod
    def from_dict(cls, data: dict, /, **kwargs: Any) -> NoReturn:
        """Event cannot be re-created."""
        raise LionAccessError(
            "An event cannot be recreated. Once it's done, it's done."
        )


class Condition(Event):
    """State evaluation."""

    @abstractmethod
    async def apply(self, *args: Any, **kwargs: Any) -> bool:
        """Apply the condition asynchronously."""


class Signal(Event):
    """a triggerable signal."""

    @abstractmethod
    async def trigger(self, *args: Any, **kwargs: Any) -> Any:
        """Trigger the signal asynchronously."""


class Action(Event):
    """An invokable action"""

    @abstractmethod
    async def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Invoke the action asynchronously."""


__all__ = ["Event", "Condition", "Signal", "Action"]


# File: lion_core/abc/_observation.py
