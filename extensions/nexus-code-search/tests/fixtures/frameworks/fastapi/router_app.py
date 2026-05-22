"""Fixture: FastAPI router-based handler set."""
from fastapi import APIRouter

router = APIRouter(prefix="/users")


@router.get("/", response_model=list)
def list_users():
    return []


@router.delete("/{user_id}")
def delete_user(user_id: int):
    return {"deleted": user_id}


@router.patch("/{user_id}")
def update_user(user_id: int, payload: dict):
    return {"updated": user_id}
