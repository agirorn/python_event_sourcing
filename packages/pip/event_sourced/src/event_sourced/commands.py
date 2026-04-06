"""Doing this and that."""

from dataclasses import dataclass
# from uuid import UUID  # noqa: TC003


@dataclass(frozen=True, slots=True)
class Command:
    aggregate_id: str


@dataclass(frozen=True, slots=True)
class AddTodo(Command):
    message: str


@dataclass(frozen=True, slots=True)
class RemoveTodo(Command):
    pass


TodoCommand = AddTodo | RemoveTodo
