"""Unit test"""

from event_sourced.commands import AddTodo, RemoveTodo


def add_todo_command() -> AddTodo:
    return AddTodo(
        aggregate_id="63db25a2-15de-437f-b093-4613f94c47b9",
        message="Do the dishes",
    )


def remove_todo_command() -> RemoveTodo:
    return RemoveTodo(
        aggregate_id="63db25a2-15de-437f-b093-4613f94c47b9",
    )
