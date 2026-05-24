from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from typing import Dict
from app.routers import tasks, users, admin

app = FastAPI(title="Task Manager API")

# Подключаем роутеры
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(admin.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ========== WEBSOCKET КОД (ДОЛЖЕН БЫТЬ) ==========

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, room_id: str, username: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][username] = websocket
        await self.broadcast(room_id, {
            "type": "system",
            "message": f"{username} joined the room"
        })
    
    def disconnect(self, room_id: str, username: str):
        if room_id in self.rooms and username in self.rooms[room_id]:
            del self.rooms[room_id][username]
            if not self.rooms[room_id]:
                del self.rooms[room_id]
    
    async def broadcast(self, room_id: str, payload: dict):
        if room_id in self.rooms:
            for username, ws in self.rooms[room_id].items():
                try:
                    await ws.send_json(payload)
                except:
                    pass
    
    def get_users(self, room_id: str) -> list:
        return list(self.rooms.get(room_id, {}).keys())

room_manager = RoomManager()

@app.websocket("/ws/rooms/{room_id}")
async def websocket_room(
    websocket: WebSocket, 
    room_id: str, 
    username: str = Query(None)
):
    if not username or not username.strip():
        await websocket.close(code=1008)
        return
    
    username = username.strip()
    await room_manager.connect(room_id, username, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                text = data.get("text", "")
                if len(text) > 300:
                    await websocket.send_json({
                        "type": "error",
                        "detail": "Message is too long"
                    })
                else:
                    await room_manager.broadcast(room_id, {
                        "type": "message",
                        "room_id": room_id,
                        "username": username,
                        "text": text
                    })
    except WebSocketDisconnect:
        room_manager.disconnect(room_id, username)
        await room_manager.broadcast(room_id, {
            "type": "system",
            "message": f"{username} left the room"
        })

@app.get("/rooms/{room_id}/users")
async def get_room_users(room_id: str):
    return {"room_id": room_id, "users": room_manager.get_users(room_id)}