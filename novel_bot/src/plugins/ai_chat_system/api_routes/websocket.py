import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import json
import logging
from websockets.exceptions import ConnectionClosed

from .. import global_state

router = APIRouter()
logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close(code=1001)
                logger.info(f"Closed existing connection for user {user_id}.")
            except (RuntimeError, ConnectionClosed):
                pass
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected.")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected.")

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    ping_task_instance = None
    try:
        async def ping_task():
            while True:
                try:
                    await asyncio.sleep(20)
                    await websocket.send_json({"type": "ping"})
                except (WebSocketDisconnect, ConnectionClosed):
                    break

        ping_task_instance = asyncio.create_task(ping_task())

        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "pong":
                    logger.debug(f"Received pong from user {user_id}")
                    continue
            except WebSocketDisconnect:
                logger.info(f"Client {user_id} disconnected gracefully.")
                break
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from user {user_id}.")
                continue

    except Exception as e:
        logger.error(f"An unexpected error in WebSocket for user {user_id}: {e}", exc_info=True)
    finally:
        if ping_task_instance:
            ping_task_instance.cancel()
        manager.disconnect(user_id)