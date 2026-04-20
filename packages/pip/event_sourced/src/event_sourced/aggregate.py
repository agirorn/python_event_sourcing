"""Doing this and that."""

import uuid
from abc import abstractmethod
from datetime import UTC, datetime  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID

from .commands import AddTodo, RemoveTodo, TodoCommand
from .error import ValidationError
from .event_store import EventStore
from .events import NoData, Snapshot, TodoAdded, TodoAddedData, TodoEvent, TodoRemoved
from .state import State

if TYPE_CHECKING:
    from .event_store import EventStore


class BaseAggregate:
    """
    The todo aggregate.

    Args:
      store: Is the event store the aggregate will use manage the aggregate.
             It will be used to replay the aggregate state and store new events.

    """

    state: State
    store: EventStore
    uncommitted_events: list[TodoEvent]
    occ_version: int = 0

    def __init__(self, store: EventStore) -> None:
        self.state = State()
        self.store = store
        self.uncommitted_events = []

    @abstractmethod
    async def execute(self, cmd: TodoCommand) -> None:
        """
        Execute a command on the aggregate.

        The command can only add new events. It can not update the aggregates
        state, that is handled by the apply functions
        """

    @abstractmethod
    def apply(self, event: TodoEvent) -> None:
        """
        Apply an event on to the aggregate.

        The apply function is the only function that should update the aggregate
        state.
        """

    def add(self, event: TodoEvent) -> None:
        """
        Add a new event to the aggregate.

        The new Event will be both applied and stored in the `uncommitted_events`
        """
        self.apply(event)
        self.append(event)

    def append(self, event: TodoEvent) -> None:
        """
        Append the events in the `uncommitted_events`.

        Appends the events to the `uncommitted_events` so the can be stored in
        the event store at the end of the command execution
        """
        self.uncommitted_events.append(event)

    async def rehydrate(self, aggregate_id: str) -> None:
        """
        Reconstitute the aggregate state from event history.

        Replays the aggregates history onto the aggregate state by applying
        events in correct order in the aggregate.
        """
        async for event in self.store.load_stream(aggregate_id):
            self.apply(event)

    def next_occ_version(self) -> int:
        """
        Return the next `occ_version`.

        Should be used when generating new events to get the next `occ_version`
        """
        return self.state.occ_version + 1

    def new_event_id(self) -> UUID:
        """Return a new event id."""
        return uuid.uuid4()


class Aggregate(BaseAggregate):
    async def execute(self, cmd: TodoCommand) -> None:
        await self.rehydrate(cmd.aggregate_id)

        match cmd:
            case AddTodo():
                if self.state.created:
                    raise ValidationError("Todo already exists")
                print("COMMAND: add todo")  # noqa: T201
                self.add(
                    TodoAdded(
                        version=1,
                        event_id=self.new_event_id(),
                        occurred_at=datetime.now(UTC),
                        occ_version=self.next_occ_version(),
                        aggregate_id=cmd.aggregate_id,
                        data=TodoAddedData(
                            message=cmd.message,
                        ),
                    )
                )
            case RemoveTodo():
                if not self.state.created:
                    raise ValidationError("Todo does not exists")
                self.add(
                    TodoRemoved(
                        version=1,
                        event_id=self.new_event_id(),
                        occurred_at=datetime.now(UTC),
                        occ_version=self.next_occ_version(),
                        aggregate_id=cmd.aggregate_id,
                        data=NoData(),
                    )
                )
        await self.store.append(self.state, self.uncommitted_events)

    def apply(self, event: TodoEvent) -> None:
        match event:
            case Snapshot():
                self.state = event.data
            case TodoAdded():
                self.state.created = True
                self.state.aggregate_id = event.aggregate_id
                self.state.occ_version = event.occ_version
            case TodoRemoved():
                self.state.occ_version = event.occ_version
