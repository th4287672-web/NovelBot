import logging
from typing import Any, Dict
from fastapi import WebSocket
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger("nonebot")

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized.")

    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        await websocket.accept()
        if user_id in self.connections:
            try:
                await self.connections[user_id].close(code=1000, reason="New connection established")
                logger.info(f"ConnectionManager: Closed existing WebSocket for user '{user_id}'.")
            except Exception:
                pass
        
        self.connections[user_id] = websocket
        logger.info(f"ConnectionManager: User '{user_id}' connected with new websocket.")

        if self.connections.get(user_id) is not websocket:
            logger.warning(f"ConnectionManager: A newer connection for user '{user_id}' arrived. Aborting outdated task.")
            return False
            
        return True

    def disconnect(self, websocket: WebSocket, user_id: str):
        if self.connections.get(user_id) == websocket:
            del self.connections[user_id]
            logger.info(f"ConnectionManager: User '{user_id}' disconnected.")

    async def send_to_user(self, user_id: str, data: Dict, current_websocket: WebSocket) -> bool:
        active_connection = self.connections.get(user_id)
        if active_connection and active_connection is current_websocket:
            try:
                await active_connection.send_json(data)
                return True
            except (ConnectionClosed, RuntimeError) as e:
                logger.warning(f"ConnectionManager: Could not send message to user '{user_id}', connection closed. Error: {e}")
                self.disconnect(active_connection, user_id)
        else:
            logger.warning(f"ConnectionManager: Suppressed message for user '{user_id}' on an outdated websocket.")
        return False

manager = ConnectionManager()

async def broadcast_status_update(message: Any, msg_type: str = "log"):
    data_to_send = {"type": msg_type, "payload": message}
    connected_sockets = list(manager.connections.items())
    for user_id, connection in connected_sockets:
        try:
            await connection.send_json(data_to_send)
        except (ConnectionClosed, RuntimeError):
            manager.disconnect(connection, user_id)