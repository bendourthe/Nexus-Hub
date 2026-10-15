### Step 7: Background Tasks and WebSockets

**Background tasks**:

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, name: str) -> None:
    """Simulate sending an email (replace with real email service)."""
    # await email_client.send(to=email, subject="Welcome!", body=f"Hello {name}")
    logger.info("Welcome email sent to %s", email)


@router.post("/register", status_code=201)
async def register(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    db: DbSession,
):
    service = UserService(db)
    user = await service.create(data)
    background_tasks.add_task(send_welcome_email, user.email, user.display_name)
    return UserResponse.model_validate(user)
```

**WebSocket endpoint**:

```python
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manage active WebSocket connections."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user left the chat")
```
