"""Fixture: Flask handlers, which share the FastAPI decorator pattern."""
from flask import Flask

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "ok"


@app.get("/health")
def health():
    return "healthy"


@app.put("/items/<int:item_id>")
def update_item(item_id):
    return {"updated": item_id}
