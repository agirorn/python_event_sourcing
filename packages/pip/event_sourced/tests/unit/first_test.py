"""Unit test"""

import pytest
from event_sourced.events import TodoAdded, TodoAddedData, TodoRemoved, NoData
from event_sourced import ValidationError
from freezegun import freeze_time

from event_sourced import Aggregate

from .commands import add_todo_command, remove_todo_command
from .test_event_store import InMemoryEventStore
from .test_time import NOW, NOW_STR
from uuid import UUID


@freeze_time(NOW_STR)
@pytest.mark.asyncio
async def test_add_todo():
    store = InMemoryEventStore()
    aggregate = Aggregate(store)
    await aggregate.command(add_todo_command())
    store.assert_events_added()
    store.assert_event_count(1)
    store.assert_event_equals(
        1,
        TodoAdded(
            version=1,
            occurred_at=NOW,
            event_id=UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6"),
            occ_version=1,
            aggregate_id="63db25a2-15de-437f-b093-4613f94c47b9",
            data=TodoAddedData(
                message="Do the dishes",
            ),
        ),
    )


@freeze_time(NOW_STR)
@pytest.mark.asyncio
async def test_add_same_to_twice():
    store = InMemoryEventStore()
    aggregate = Aggregate(store)
    await aggregate.command(add_todo_command())
    store.assert_event_count(1)
    store.assert_event_equals(
        1,
        TodoAdded(
            version=1,
            occurred_at=NOW,
            event_id=UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6"),
            occ_version=1,
            aggregate_id="63db25a2-15de-437f-b093-4613f94c47b9",
            data=TodoAddedData(
                message="Do the dishes",
            ),
        ),
    )
    store.start_tracking()
    aggregate = Aggregate(store)
    with pytest.raises(ValidationError, match="Todo already exist"):
        await aggregate.command(add_todo_command())
    store.assert_no_events_added()


@freeze_time(NOW_STR)
@pytest.mark.asyncio
async def test_remove_todo_when_no_todo_exists():
    store = InMemoryEventStore()
    aggregate = Aggregate(store)
    with pytest.raises(ValidationError, match="Todo does not exisit"):
        await aggregate.command(remove_todo_command())
    store.assert_no_events_added()


@freeze_time(NOW_STR)
@pytest.mark.asyncio
async def test_remove_todo():
    store = InMemoryEventStore()
    aggregate = Aggregate(store)
    await aggregate.command(add_todo_command())
    store.start_tracking()
    aggregate = Aggregate(store)
    await aggregate.command(remove_todo_command())
    store.assert_events_added()
    store.assert_event_count(2)
    store.assert_event_equals(
        2,
        TodoRemoved(
            version=1,
            event_id=UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6"),
            occurred_at=NOW,
            occ_version=2,
            aggregate_id="63db25a2-15de-437f-b093-4613f94c47b9",
            data=NoData(),
        ),
    )
