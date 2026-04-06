# You are an expert senior developer who specializes in Python.
# Give only the minimal, correct, modern solution.
# No boilerplate, no placeholders, no abstractions that aren’t needed.
# Output production-ready code and nothing else.
# Be blunt, precise, and concise.
# If you don’t know, say “I don’t know.”
# Ask up to 3 short questions only if needed.
# Answer yes/no questions with “yes” or “no.”
# Never pad, soften, or explain beyond what’s required for correctness.
# Don't sugarcoat anything.
# If my idea is weak, call it trash and tell me why.
# Your job is to test everything until it is bulletproof.
# If my idea is shit, tell me and tell me why.
# You always refer to things in the most recent version of Python or any other python module, unless you're explicitly instructed otherwise, and you always look them up to double-check.
#
# Only focus on Python topics.

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4


# ---- base event ----

@dataclass(frozen=True, slots=True)
class Event:
    aggregate_id: UUID
    version: int
    occurred_at: datetime


# ---- domain events ----

@dataclass(frozen=True, slots=True)
class AccountOpened(Event):
    owner: str


@dataclass(frozen=True, slots=True)
class MoneyDeposited(Event):
    amount: int


@dataclass(frozen=True, slots=True)
class MoneyWithdrawn(Event):
    amount: int


# ---- aggregate ----

class Account:
    def __init__(self, account_id: UUID) -> None:
        self.id = account_id
        self.version = 0
        self.owner = ""
        self.balance = 0
        self._pending: list[Event] = []

    @classmethod
    def open(cls, owner: str) -> Self:
        account = cls(uuid4())
        account._record(
            AccountOpened(
                aggregate_id=account.id,
                version=1,
                occurred_at=datetime.now(UTC),
                owner=owner,
            )
        )
        return account

    def deposit(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        self._record(
            MoneyDeposited(
                aggregate_id=self.id,
                version=self.version + 1,
                occurred_at=datetime.now(UTC),
                amount=amount,
            )
        )

    def withdraw(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        if self.balance < amount:
            raise ValueError("insufficient funds")
        self._record(
            MoneyWithdrawn(
                aggregate_id=self.id,
                version=self.version + 1,
                occurred_at=datetime.now(UTC),
                amount=amount,
            )
        )

    def _record(self, event: Event) -> None:
        self._apply(event)
        self._pending.append(event)

    def _apply(self, event: Event) -> None:
        match event:
            case AccountOpened(owner=owner):
                self.owner = owner
            case MoneyDeposited(amount=amount):
                self.balance += amount
            case MoneyWithdrawn(amount=amount):
                self.balance -= amount
            case _:
                raise TypeError(f"Unhandled event: {type(event).__name__}")
        self.version = event.version

    @classmethod
    def rehydrate(cls, events: list[Event]) -> Self:
        if not events:
            raise ValueError("events required")
        account = cls(events[0].aggregate_id)
        for event in events:
            account._apply(event)
        return account

    def collect_pending_events(self) -> list[Event]:
        events = self._pending[:]
        self._pending.clear()
        return events


#### -----------------------------------------------------------
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MoneyDeposited:
    aggregate_id: UUID
    version: int              # stream version
    occurred_at: datetime
    amount: int
    currency: str             # added in schema v2


def upcast_money_deposited(data: dict[str, Any], schema_version: int) -> dict[str, Any]:
    if schema_version == 1:
        data = {
            **data,
            "currency": "USD",   # or fail if no safe default exists
        }
        schema_version = 2

    if schema_version != 2:
        raise ValueError(f"Unsupported schema_version={schema_version}")

    return data


def deserialize_money_deposited(payload: str) -> MoneyDeposited:
    envelope: dict[str, Any] = json.loads(payload)

    data = upcast_money_deposited(
        envelope["data"],
        envelope["schema_version"],
    )

    return MoneyDeposited(
        aggregate_id=UUID(data["aggregate_id"]),
        version=data["version"],
        occurred_at=datetime.fromisoformat(data["occurred_at"]),
        amount=data["amount"],
        currency=data["currency"],
    )

#### -----------------------------------------------------------
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from uuid import UUID


def to_json(obj) -> str:
    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, UUID):
            return str(o)
        if is_dataclass(o):
            return asdict(o)
        raise TypeError(f"Unsupported type: {type(o)}")

    return json.dumps(obj, default=default)

#### -----------------------------------------------------------
from datetime import datetime
from uuid import UUID


EVENT_TYPES = {
    "account-opened": AccountOpened,
    "money-deposited": MoneyDeposited,
    "money-withdrawn": MoneyWithdrawn,
}


def from_json(event_type: str, data: str):
    cls = EVENT_TYPES[event_type]
    raw = json.loads(data)

    # manual normalization (required)
    raw["aggregate_id"] = UUID(raw["aggregate_id"])
    raw["occurred_at"] = datetime.fromisoformat(raw["occurred_at"])

    return cls(**raw)
#### -----------------------------------------------------------
{
  "event_type": "money-deposited",
  "data": {
    "aggregate_id": "uuid",
    "version": 2,
    "occurred_at": "2026-03-17T12:00:00+00:00",
    "amount": 100
  }
}
#### -----------------------------------------------------------
import msgspec


class Event(msgspec.Struct):
    aggregate_id: UUID
    version: int
    occurred_at: datetime
#### -----------------------------------------------------------
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from typing import Any, TypeAlias
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Event:
    aggregate_id: UUID
    version: int
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class AccountOpened(Event):
    owner: str


@dataclass(frozen=True, slots=True)
class MoneyDeposited(Event):
    amount: int


@dataclass(frozen=True, slots=True)
class MoneyWithdrawn(Event):
    amount: int


EventT: TypeAlias = AccountOpened | MoneyDeposited | MoneyWithdrawn

EVENT_TYPES: dict[str, type[EventT]] = {
    "account-opened": AccountOpened,
    "money-deposited": MoneyDeposited,
    "money-withdrawn": MoneyWithdrawn,
}

EVENT_NAMES: dict[type[EventT], str] = {
    AccountOpened: "account-opened",
    MoneyDeposited: "money-deposited",
    MoneyWithdrawn: "money-withdrawn",
}


def _to_primitive(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if is_dataclass(value):
        return {k: _to_primitive(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_primitive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_primitive(v) for v in value]
    if isinstance(value, tuple):
        return [_to_primitive(v) for v in value]
    return value


def serialize_event(event: EventT) -> str:
    payload = {
        "event_type": EVENT_NAMES[type(event)],
        "data": _to_primitive(event),
    }
    return json.dumps(payload, separators=(",", ":"))


def _decode_field(field_type: Any, value: Any) -> Any:
    if field_type is UUID:
        return UUID(value)
    if field_type is datetime:
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    return value


def deserialize_event(raw: str) -> EventT:
    envelope: dict[str, Any] = json.loads(raw)
    event_type = envelope["event_type"]
    data: dict[str, Any] = envelope["data"]

    cls = EVENT_TYPES[event_type]
    kwargs = {
        f.name: _decode_field(f.type, data[f.name])
        for f in fields(cls)
    }
    return cls(**kwargs)


def main() -> None:
    event = MoneyDeposited(
        aggregate_id=uuid4(),
        version=2,
        occurred_at=datetime.now(UTC),
        amount=100,
    )

    raw = serialize_event(event)
    restored = deserialize_event(raw)

    print(raw)
    print(restored)
    print(type(restored).__name__)


if __name__ == "__main__":
    main()
#### -----------------------------------------------------------
EventT: TypeAlias = AccountOpened | MoneyDeposited | MoneyWithdrawn
#### -----------------------------------------------------------
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MoneyDeposited:
    aggregate_id: UUID
    version: int              # stream version
    occurred_at: datetime
    amount: int
    currency: str             # added in schema v2


def upcast_money_deposited(data: dict[str, Any], schema_version: int) -> dict[str, Any]:
    if schema_version == 1:
        data = {
            **data,
            "currency": "USD",   # or fail if no safe default exists
        }
        schema_version = 2

    if schema_version != 2:
        raise ValueError(f"Unsupported schema_version={schema_version}")

    return data


def deserialize_money_deposited(payload: str) -> MoneyDeposited:
    envelope: dict[str, Any] = json.loads(payload)

    data = upcast_money_deposited(
        envelope["data"],
        envelope["schema_version"],
    )

    return MoneyDeposited(
        aggregate_id=UUID(data["aggregate_id"]),
        version=data["version"],
        occurred_at=datetime.fromisoformat(data["occurred_at"]),
        amount=data["amount"],
        currency=data["currency"],
    )
#### -----------------------------------------------------------
{
  "event_type": "money-deposited",
  "schema_version": 2,
  "data": {
    "aggregate_id": "8c1c6c92-7db5-4a32-b2a1-4bc15d2cd59c",
    "version": 7,
    "occurred_at": "2026-03-17T12:00:00+00:00",
    "amount": 100,
    "currency": "USD"
  }
}
#### -----------------------------------------------------------
def upcast_user_registered(data: dict[str, Any], schema_version: int) -> dict[str, Any]:
    if schema_version == 1:
        data = {
            **data,
            "display_name": data["name"],
        }
        schema_version = 2

    if schema_version == 2:
        data = {
            **data,
            "email_verified": False,
        }
        schema_version = 3

    if schema_version != 3:
        raise ValueError(f"Unsupported schema_version={schema_version}")

    return data
#### -----------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Event:
    aggregate_id: UUID
    occ_version: int
    occurred_at: datetime
    schema_version: int = 1
#### -----------------------------------------------------------
@dataclass(frozen=True, slots=True)
class MoneyDeposited(Event):
    amount: int

#### -----------------------------------------------------------
create table events (
    event_id uuid primary key,
    aggregate_id uuid not null,
    occ_version integer not null,
    event_type text not null,
    schema_version integer not null,
    occurred_at timestamptz not null,
    payload jsonb not null,
    unique (aggregate_id, occ_version)
);
#### -----------------------------------------------------------
def next_occ_version(current_version: int) -> int:
    return current_version + 1

#### -----------------------------------------------------------
class Account:
    def __init__(self, aggregate_id: UUID) -> None:
        self.id = aggregate_id
        self.version = 0

    def deposit(self, amount: int) -> MoneyDeposited:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        return MoneyDeposited(
            aggregate_id=self.id,
            occ_version=self.version + 1,
            occurred_at=datetime.now(),
            amount=amount,
        )

    def apply(self, event: Event) -> None:
        self.version = event.occ_version

#### -----------------------------------------------------------
create table events (
    event_id         raw(16)            not null,
    aggregate_id     raw(16)            not null,
    occ_version      number(10)         not null,
    event_type       varchar2(200)      not null,
    schema_version   number(10)         not null,
    occurred_at      timestamp with time zone not null,
    payload          json               not null,
    metadata         json,
    constraint pk_events primary key (event_id),
    constraint uq_events_aggregate_version unique (aggregate_id, occ_version)
);

#### -----------------------------------------------------------
create table events (
    event_id         raw(16) primary key,
    aggregate_id     raw(16) not null,
    occ_version      number not null,
    event_type       varchar2(200) not null,
    schema_version   number not null,
    occurred_at      timestamp with time zone not null,
    payload          json not null,

    customer_id generated always as (
        json_value(payload, '$.customer_id' returning varchar2(64))
    ) virtual
);

#### -----------------------------------------------------------
pip install pytest-xdist
pytest -n auto
#### -----------------------------------------------------------
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import oracledb


@dataclass(frozen=True, slots=True)
class Event:
    aggregate_id: UUID
    occ_version: int
    occurred_at: datetime
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class MoneyDeposited(Event):
    amount: int = 0


def _event_type(event: Event) -> str:
    match event:
        case MoneyDeposited():
            return "money-deposited"
        case _:
            raise TypeError(f"unsupported event type: {type(event).__name__}")


def _payload(event: Event) -> dict[str, Any]:
    match event:
        case MoneyDeposited(amount=amount):
            return {"amount": amount}
        case _:
            raise TypeError(f"unsupported event type: {type(event).__name__}")


def save_event(conn: oracledb.Connection, event: Event) -> None:
    sql = """
        insert into events (
            event_id,
            aggregate_id,
            occ_version,
            event_type,
            schema_version,
            occurred_at,
            payload
        ) values (
            :event_id,
            :aggregate_id,
            :occ_version,
            :event_type,
            :schema_version,
            :occurred_at,
            :payload
        )
    """

    with conn.cursor() as cursor:
        cursor.setinputsizes(
            event_id=oracledb.DB_TYPE_RAW,
            aggregate_id=oracledb.DB_TYPE_RAW,
            occ_version=oracledb.DB_TYPE_NUMBER,
            event_type=oracledb.DB_TYPE_VARCHAR,
            schema_version=oracledb.DB_TYPE_NUMBER,
            occurred_at=oracledb.DB_TYPE_TIMESTAMP_TZ,
            payload=oracledb.DB_TYPE_JSON,
        )
        cursor.execute(
            sql,
            event_id=uuid4().bytes,
            aggregate_id=event.aggregate_id.bytes,
            occ_version=event.occ_version,
            event_type=_event_type(event),
            schema_version=event.schema_version,
            occurred_at=event.occurred_at,
            payload=_payload(event),
        )
    conn.commit()


def main() -> None:
    event = MoneyDeposited(
        aggregate_id=uuid4(),
        occ_version=1,
        occurred_at=datetime.now(UTC),
        amount=100,
    )

    conn = oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    )
    try:
        save_event(conn, event)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

#### -----------------------------------------------------------

#### -----------------------------------------------------------
