"""Unit test"""

from event_sourced.commands import AddTodo, RemoveTodo


def add_todo_command() -> AddTodo:
    return AddTodo(
        aggregate_id="todo-1",
        message="Do the dishes",
    )


def remove_todo_command() -> RemoveTodo:
    return RemoveTodo(
        aggregate_id="todo-1",
    )
