"""Doing this and that."""

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from logic import hello_message


class HelloRequest(BaseModel):
    """Doing this and that."""

    model_config = ConfigDict(extra="forbid")
    name: str


class HelloResponse(BaseModel):
    """Doing this and that."""

    msg: str


class RootResponse(BaseModel):
    """Doing this and that."""

    msg: str


app = FastAPI()


@app.get("/")
def get_root() -> RootResponse:
    """Doing this and that."""
    return RootResponse(msg="ok")


@app.post("/hello")
def post_hello(body: HelloRequest) -> HelloResponse:
    """Doing this and that."""
    return HelloResponse(msg=hello_message(body.name))
