"""Doing this and that."""

from datetime import UTC, datetime  # noqa: TC003
from typing import TYPE_CHECKING

from .commands import AddTodo, RemoveTodo, TodoCommand
from .event_store import EventStore
from .events import TodoAdded, TodoRemoved, TodoAddedData, TodoEvent, NoData
from .state import State
from .error import ValidationError
import uuid
from uuid import UUID

if TYPE_CHECKING:
    from .event_store import EventStore


class Aggregate:
    """
    The todo aggregate.

    Args:
      store: Is the event store the aggregate will use manage the aggregate.
             It will be used to replay the agregates state and store new events.

    """

    state: State
    store: EventStore
    uncomitted_events: list[TodoEvent]
    occ_version: int = 0

    def __init__(self, store: EventStore) -> None:
        self.state = State()
        self.store = store
        self.uncomitted_events = []

    async def command(self, cmd: TodoCommand) -> None:
        await self.rehydrate(cmd.aggregate_id)

        match cmd:
            case AddTodo():
                if self.state.created:
                    raise ValidationError("Todo already exist")
                print("COMMAND: add todo")  # noqa: T201
                self.save(
                    TodoAdded(
                        version=1,
                        event_id=self.new_event_id(),
                        occurred_at=datetime.now(UTC),
                        occ_version=self.new_occ_version(),
                        aggregate_id=cmd.aggregate_id,
                        data=TodoAddedData(
                            message=cmd.message,
                        ),
                    )
                )
            case RemoveTodo():
                if not self.state.created:
                    raise ValidationError("Todo does not exisit")
                self.save(
                    TodoRemoved(
                        version=1,
                        event_id=self.new_event_id(),
                        occurred_at=datetime.now(UTC),
                        occ_version=self.new_occ_version(),
                        aggregate_id=cmd.aggregate_id,
                        data=NoData(),
                    )
                )
        await self.store.append(self.state, self.uncomitted_events)

    def save(self, event: TodoEvent) -> None:
        self.apply(event)
        self.append(event)

    def append(self, event: TodoEvent) -> None:
        self.uncomitted_events.append(event)

    def apply(self, event: TodoEvent) -> None:
        match event:
            case TodoAdded():
                self.state.created = True
                self.state.aggregate_id = event.aggregate_id
                self.state.occ_version = event.occ_version
            case TodoRemoved():
                self.state.occ_version = event.occ_version

    async def rehydrate(self, aggregate_id: str) -> None:
        async for event in self.store.load_stream(aggregate_id):
            self.apply(event)

    def new_occ_version(self) -> int:
        return self.state.occ_version + 1

    def new_event_id(self) -> UUID:
        return uuid.uuid4()
