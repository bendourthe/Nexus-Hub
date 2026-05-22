"""Fixture: FastAPI app with @app decorators on multiple HTTP methods."""
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"hello": "world"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}


@app.post("/items")
def create_item(name: str):
    return {"created": name}
