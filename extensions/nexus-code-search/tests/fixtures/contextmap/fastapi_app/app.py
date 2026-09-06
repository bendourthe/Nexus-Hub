"""FastAPI accuracy fixture: routes + env + middleware with a decoy."""
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

DATABASE_URL = os.environ["DATABASE_URL"]
PORT = os.getenv("PORT", "8000")
# Decoy: a plain dict access that must NOT be picked up as an env var.
NOT_ENV = some_config["NOT_ENV"]


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return session.query(Item).get(item_id)


@app.post("/pay")
def pay(user=Depends(get_current_user)):
    return stripe.checkout.session.create()
