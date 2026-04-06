"""Doing this and that."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from event_sourced.events import TodoEvent
    from event_sourced.state import State

from event_sourced import EventStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class InMemoryEventStore(EventStore):
    states: dict[str, State]
    events: list[TodoEvent]
    last_count: int

    def __init__(self) -> None:
        self.last_count = 0
        self._streams: dict[str, list[TodoEvent]] = {}
        self.events = []
        self.states = {}

    async def load_stream(self, aggregate_id: str) -> AsyncIterator[TodoEvent]:
        for event in self.events:
            if event.aggregate_id == aggregate_id:
                yield event

    async def append(self, state: State, events: list[TodoEvent]) -> None:
        self.states[state.aggregate_id] = state
        self.events.extend(events)

    def assert_event_count(self, count: int) -> None:
        actual = len(self.events)
        assert actual == count, f"Event count({actual}) should have been {count}"

    def assert_event_equals(self, index: int, expected: TodoEvent) -> None:
        actual = self.events[index - 1]
        # Intentionaly overwriting this here instead of mocking all the tests
        # and also using the self.new_event_id() method for all uuid generation
        # in the Aggregate code
        expected.event_id = actual.event_id
        assert actual == expected, f"Event ({actual}) at {index} should equal {expected}"

    def start_tracking(self) -> None:
        self.last_count = len(self.events)

    def assert_no_events_added(self) -> None:
        actual = len(self.events)
        expected = self.last_count
        added = actual - expected
        e_name = "events"
        if added == 1:
            e_name = "event"
        assert actual == expected, f"{added} {e_name} was added since tracking started"

    def assert_events_added_count(self, count: int) -> None:
        actual = len(self.events) - self.last_count
        assert actual == count, f"Added event count({actual}) should have been {count}"

    def assert_events_added(self) -> None:
        actual = len(self.events)
        expected = self.last_count
        assert actual > expected, "No events where added to the eventstore"
