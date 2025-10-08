from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from routers import main_router
from starlette.middleware.sessions import SessionMiddleware
app = FastAPI()
app.include_router(main_router)
app.add_middleware(SessionMiddleware, secret_key="b47a1d6f8f04e5c9298b9c6e52a27f3db7c4d9a11d2e80b4bb1e3a63c918fae2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple test WebSocket endpoint
@app.websocket("/test-ws")
async def test_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("WebSocket connection successful!")
    await websocket.close()

# Simple storage for WebSocket connections
chat_clients = {}  # WebSocket -> username
chat_rooms = {}    # room -> {WebSocket -> username}

async def broadcast_to_room(message: dict, room: str, sender: WebSocket = None):
    if room not in chat_rooms:
        return
    dead_clients = []
    for ws in chat_rooms[room]:
        if ws != sender:  # Don't send back to sender
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead_clients.append(ws)
    # Clean up dead connections
    for dc in dead_clients:
        chat_rooms[room].pop(dc, None)
        chat_clients.pop(dc, None)

# Direct WebSocket for chat - bypass all middleware
@app.websocket("/chat-ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected to /chat-ws")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket data: {data}")

            try:
                msg = json.loads(data)
                user = chat_clients.get(websocket, None)
                room = msg.get("room", "default")

                if msg["type"] == "join":
                    username = msg.get("user", "Anonymous")
                    chat_clients[websocket] = username

                    # Add to room
                    if room not in chat_rooms:
                        chat_rooms[room] = {}
                    chat_rooms[room][websocket] = username

                    # Broadcast online users
                    online_users = list(chat_rooms.get(room, {}).values())
                    await broadcast_to_room({
                        "type": "online_users",
                        "users": online_users,
                        "count": len(online_users),
                        "room": room
                    }, room=room)

                    print(f"User {username} joined room {room}")

                elif msg["type"] == "call_initiate" and user:
                    print(f"Call initiated by {user} in room {room}")
                    await broadcast_to_room({
                        "type": "call_initiate",
                        "from": user,
                        "callType": msg.get("callType", "audio"),
                        "room": room
                    }, room=room, sender=websocket)

                elif msg["type"] == "call_accept" and user:
                    print(f"Call accepted by {user} in room {room}")
                    await broadcast_to_room({
                        "type": "call_accept",
                        "from": user,
                        "room": room
                    }, room=room, sender=websocket)

                elif msg["type"] == "call_reject" and user:
                    print(f"Call rejected by {user} in room {room}")
                    await broadcast_to_room({
                        "type": "call_reject",
                        "from": user,
                        "room": room
                    }, room=room, sender=websocket)

                elif msg["type"] == "call_end" and user:
                    print(f"Call ended by {user} in room {room}")
                    await broadcast_to_room({
                        "type": "call_end",
                        "from": user,
                        "room": room
                    }, room=room, sender=websocket)

                elif msg["type"] == "webrtc_offer" and user:
                    print(f"WebRTC offer from {user} in room {room}")
                    await broadcast_to_room({
                        "type": "webrtc_offer",
                        "from": user,
                        "offer": msg.get("offer"),
                        "room": room
                    }, room=room, sender=websocket)

                elif msg["type"] == "webrtc_answer" and user:
                    print(f"WebRTC answer from {user} in room {room}")
                    await broadcast_to_room({
                        "type": "webrtc_answer",
                        "from": user,
                        "answer": msg.get("answer"),
                        "room": room
                    }, room=room, sender=websocket)

                elif msg["type"] == "webrtc_ice_candidate" and user:
                    print(f"ICE candidate from {user} in room {room}")
                    await broadcast_to_room({
                        "type": "webrtc_ice_candidate",
                        "from": user,
                        "candidate": msg.get("candidate"),
                        "room": room
                    }, room=room, sender=websocket)

            except json.JSONDecodeError:
                print(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        print("WebSocket disconnected")
        username = chat_clients.pop(websocket, None)
        if username:
            for room_name, members in chat_rooms.items():
                if websocket in members:
                    members.pop(websocket, None)
                    # Broadcast updated online users
                    online_users = list(chat_rooms.get(room_name, {}).values())
                    await broadcast_to_room({
                        "type": "online_users",
                        "users": online_users,
                        "count": len(online_users),
                        "room": room_name
                    }, room=room_name)
    except Exception as e:
        print(f"WebSocket error: {e}")
        username = chat_clients.pop(websocket, None)
        print(f"Cleaned up connection for user: {username}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)