from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Generic, Self, TypeVar
from uuid import UUID, uuid4

# ---------- events ----------

@dataclass(frozen=True, slots=True)
class Event:
    aggregate_id: UUID
    occ_version: int
    occurred_at: datetime
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class AccountOpened(Event):
    owner: str = ""


@dataclass(frozen=True, slots=True)
class MoneyDeposited(Event):
    amount: int = 0


AccountEvent = AccountOpened | MoneyDeposited
E = TypeVar("E", bound=Event)


# ---------- event store ----------

# class ConcurrencyError(Exception):
#     pass

class ConcurrencyError(Exception):
    def __init__(self, expected_version: int, current_version: int) -> None:
        super().__init__(
            f"expected version {expected_version}, got {current_version}"
        )


class EventStore(ABC, Generic[E]):
    @abstractmethod
    def load_stream(self, aggregate_id: UUID) -> list[E]:
        raise NotImplementedError

    @abstractmethod
    def append(self, aggregate_id: UUID, expected_version: int, events: list[E]) -> None:
        raise NotImplementedError


class InMemoryEventStore(EventStore[E]):
    def __init__(self) -> None:
        self._streams: dict[UUID, list[E]] = {}

    def load_stream(self, aggregate_id: UUID) -> list[E]:
        return list(self._streams.get(aggregate_id, []))

    def append(self, aggregate_id: UUID, expected_version: int, events: list[E]) -> None:
        stream = self._streams.setdefault(aggregate_id, [])
        current_version = stream[-1].occ_version if stream else 0
        if current_version != expected_version:
            raise ConcurrencyError(
                expected_version, current_version
            )
        stream.extend(events)


# ---------- aggregate base ----------

AE = TypeVar("AE", bound=Event)


class Aggregate(ABC, Generic[AE]):
    def __init__(self, aggregate_id: UUID) -> None:
        self.id = aggregate_id
        self.version = 0
        self._pending: list[AE] = []

    @classmethod
    def rehydrate(cls, events: list[AE]) -> Self:
        if not events:
            raise RequiredEventError
        aggregate = cls(events[0].aggregate_id)
        for event in events:
            aggregate._apply(event)
        return aggregate

    def collect_pending_events(self) -> list[AE]:
        pending = self._pending[:]
        self._pending.clear()
        return pending

    def _record(self, event: AE) -> None:
        self._apply(event)
        self._pending.append(event)

    @abstractmethod
    def _apply(self, event: AE) -> None:
        raise NotImplementedError


class RequiredEventError(ValueError): # Inherit from an appropriate built-in exception
    def __init__(self) -> None:
        super().__init__("events required")

# ---------- concrete aggregate ----------

class Account(Aggregate[AccountEvent]):
    def __init__(self, aggregate_id: UUID) -> None:
        super().__init__(aggregate_id)
        self.owner = ""
        self.balance = 0

    @classmethod
    def open(cls, owner: str) -> Account:
        if not owner:
            raise ValueError("owner is required")
        account = cls(uuid4())
        account._record(
            AccountOpened(
                aggregate_id=account.id,
                occ_version=1,
                occurred_at=datetime.now(UTC),
                owner=owner,
            )
        )
        return account

    @classmethod
    def load(cls, store: EventStore[AccountEvent], aggregate_id: UUID) -> Account:
        return cls.rehydrate(store.load_stream(aggregate_id))

    def save(self, store: EventStore[AccountEvent]) -> None:
        pending = self.collect_pending_events()
        if not pending:
            return
        expected_version = pending[0].occ_version - 1
        store.append(self.id, expected_version, pending)

    def deposit(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        self._record(
            MoneyDeposited(
                aggregate_id=self.id,
                occ_version=self.version + 1,
                occurred_at=datetime.now(UTC),
                amount=amount,
            )
        )

    def _apply(self, event: AccountEvent) -> None:
        match event:
            case AccountOpened(owner=owner):
                self.owner = owner
            case MoneyDeposited(amount=amount):
                self.balance += amount
            case _:
                raise TypeError(f"unhandled event: {type(event).__name__}")
        self.version = event.occ_version


# ---------- unit tests ----------

def test_account_open_and_save() -> None:
    store = InMemoryEventStore[AccountEvent]()

    account = Account.open("alice")
    account.save(store)

    stream = store.load_stream(account.id)

    assert len(stream) == 1
    assert isinstance(stream[0], AccountOpened)
    assert account.version == 1
    assert account.owner == "alice"


def test_account_rehydrate_and_deposit() -> None:
    store = InMemoryEventStore[AccountEvent]()

    account = Account.open("alice")
    account.save(store)

    loaded = Account.load(store, account.id)
    loaded.deposit(100)
    loaded.save(store)

    reloaded = Account.load(store, account.id)

    assert reloaded.owner == "alice"
    assert reloaded.balance == 100
    assert reloaded.version == 2


def test_concurrency_error() -> None:
    store = InMemoryEventStore[AccountEvent]()

    account = Account.open("alice")
    account.save(store)

    a = Account.load(store, account.id)
    b = Account.load(store, account.id)

    a.deposit(100)
    a.save(store)

    b.deposit(50)

    try:
        b.save(store)
    except ConcurrencyError:
        pass
    else:
        raise AssertionError("expected ConcurrencyError")
