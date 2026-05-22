from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"hello": "world"}


@app.post("/items")
def create_item(name: str):
    return {"name": name}


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"deleted": item_id}
