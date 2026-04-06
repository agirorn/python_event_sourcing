"""Doing this and that."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .events import TodoEvent
    from .state import State
    from collections.abc import AsyncIterator


class EventStore(ABC):
    @abstractmethod
    def load_stream(self, aggregate_id: str) -> AsyncIterator[TodoEvent]:
        """
        Load in all events for a the agregate.

        The returned valure is a stream of events that can be itterated over one
        by one to reduce memmory consumption and backpreasure on the system.
        """

    @abstractmethod
    async def append(self, state: State, events: list[TodoEvent]) -> None:
        """
        Apend events to the event stream.

        TODO: check f we need the accregate id here. Probablay better to have
        this just generic and have it write to the steam
        """


class ConcurrencyError(Exception):
    def __init__(self, expected_version: int, current_version: int) -> None:
        super().__init__(f"expected version {expected_version}, got {current_version}")
