import base64
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from minio import Minio
from motor.motor_asyncio import AsyncIOMotorClient

from core import settings

router = APIRouter()
clients: dict[WebSocket, str] = {}  # WebSocket -> username
MONGO_URL = f"mongodb://{settings.MONGO_INITDB_ROOT_USERNAME}:{settings.MONGO_INITDB_ROOT_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}"
client = AsyncIOMotorClient(MONGO_URL)

db = client["chat_app"]
messages_collection = db["messages"]
rooms_collection = db["rooms"]
avatars_collection = db["avatars"]

# Bộ nhớ tạm trong RAM để quản lý websocket kết nối theo room
rooms: dict[str, dict[WebSocket, str]] = {}

minio_client = Minio(
    settings.MINIO_ENDPOINT.replace("https://", ""),
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=True
)
BUCKET_NAME = "chat-images"
# Tạo bucket nếu chưa có
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME, location="")

async def broadcast(message: dict, room: str, sender: WebSocket = None):
    if room not in rooms:
        return
    dead_clients = []
    for ws in rooms[room]:
        try:
            await ws.send_text(json.dumps(message, default=str))
        except Exception:
            dead_clients.append(ws)
    for dc in dead_clients:
        rooms[room].pop(dc, None)


def safe_b64decode(data: str) -> bytes:
    # Bỏ tiền tố "data:image/png;base64," nếu có
    if data.startswith("data:"):
        data = data.split(",", 1)[1]

    # Thêm padding nếu thiếu
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)

    return base64.b64decode(data)

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user = clients.get(websocket, None)
            room = msg.get("room", "default")

            # ---- JOIN ROOM ----
            if msg["type"] == "join":
                username = msg.get("user", "Ẩn danh")
                clients[websocket] = username

                # Thêm vào RAM
                if room not in rooms:
                    rooms[room] = {}
                rooms[room][websocket] = username
                # Broadcast current online count
                online_users = list(rooms.get(room, {}).values())
                await broadcast({
                    "type": "online_users",
                    "users": online_users,
                    "count": len(online_users),
                    "room": room
                }, room=room)

                # Kiểm tra DB rooms
                exists = await rooms_collection.find_one({"room": room})
                if not exists:
                    doc = {
                        "room": room,
                        "members": [username],
                        "messages": []  # lưu danh sách message_id
                    }
                    await rooms_collection.insert_one(doc)
                else:
                    await rooms_collection.update_one(
                        {"room": room},
                        {"$addToSet": {"members": username}}
                    )

                await broadcast(
                    {"type": "join", "user": username, "room": room},
                    room=room,
                    sender=websocket
                )

            # ---- TYPING ----
            elif msg["type"] == "typing" and user:
                await broadcast({
                    "type": "typing",
                    "user": user,
                    "typing": msg.get("typing", False),
                }, sender=websocket, room=room)

            # ---- REACTION ----
            elif msg["type"] == "reaction" and user:
                action = msg.get("action", "add")
                message_id = ObjectId(msg.get("messageId"))
                emoji = msg.get("emoji")

                if action == "add":
                    await messages_collection.update_one(
                        {"_id": message_id},
                        {"$addToSet": {"reactions": {"user": user, "emoji": emoji}}}
                    )
                elif action == "remove":
                    await messages_collection.update_one(
                        {"_id": message_id},
                        {"$pull": {"reactions": {"user": user, "emoji": emoji}}}
                    )

                await broadcast({
                    "type": "reaction",
                    "messageId": str(message_id),
                    "user": user,
                    "emoji": emoji,
                    "action": action,
                }, sender=websocket, room=room)


            # ---- CHAT MESSAGE ----
            elif msg["type"] == "chat" and user:
                avatar_url = msg.get("avatarUrl")
                # Xử lý upload ảnh vào MinIO
                image_urls = []
                for img_base64 in (msg.get("images") or []):
                    try:
                        # img_base64 là chuỗi base64, convert thành bytes
                        img_bytes = safe_b64decode(img_base64)
                        file_id = str(uuid.uuid4())
                        object_name = f"{room}/{file_id}.png"

                        # upload lên MinIO
                        minio_client.put_object(
                            BUCKET_NAME,
                            object_name,
                            io.BytesIO(img_bytes),
                            length=len(img_bytes),
                            content_type="image/png"
                        )

                        url = f"{settings.MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"
                        image_urls.append(url)
                    except Exception as e:
                        print("Upload image error:", e)
                chat_msg = {
                    "type": "chat",
                    "user": user,
                    "avatarUrl": avatar_url,
                    "room": room,
                    "text": msg.get("text", ""),
                    "images": image_urls,  # chỉ lưu URL
                    "replyTo": msg.get("replyTo") if isinstance(msg.get("replyTo"), dict) else None,
                    "timestamp": datetime.now(timezone(timedelta(hours=7))),
                }
                # Lưu vào MongoDB
                result = await messages_collection.insert_one(chat_msg)
                message_id = str(result.inserted_id)

                # Lưu message_id vào rooms_collection
                await rooms_collection.update_one(
                    {"room": room},
                    {"$push": {"messages": message_id}}
                )

                # Gửi broadcast
                chat_msg["id"] = message_id
                chat_msg["timestamp"] = chat_msg["timestamp"].isoformat()
                await broadcast(chat_msg, room=room, sender=websocket)

            # ---- EDIT MESSAGE ----
            elif msg["type"] == "edit" and user:
                avatar_url = msg.get("avatarUrl")
                await messages_collection.update_one(
                    {"_id": ObjectId(msg.get("messageId")), "user": user},
                    {"$set": {
                        "text": msg.get("text", ""),
                        "edited": True,
                        "avatarUrl": avatar_url,
                        "images": msg.get("images", [])
                    }}
                )
                await broadcast({
                    "type": "edit",
                    "messageId": msg.get("messageId"),
                    "text": msg.get("text", ""),
                    "images": msg.get("images", []),
                    "avatarUrl": avatar_url,
                    "user": user,
                }, room=room)

            # ---- DELETE MESSAGE ----
            elif msg["type"] == "delete" and user:
                message_id = msg.get("messageId")
                if not message_id:
                    continue

                message_doc = await messages_collection.find_one(
                    {"_id": ObjectId(message_id), "user": user}
                )

                if message_doc:
                    # Kiểm tra nếu có ảnh hoặc audio thì xóa trong MinIO
                    files_to_delete = []

                    # Có thể có nhiều ảnh
                    if isinstance(message_doc.get("images"), list):
                        files_to_delete.extend(message_doc["images"])

                    # Có thể có file audio
                    if message_doc.get("audio"):
                        files_to_delete.append(message_doc["audio"])

                    for file_url in files_to_delete:
                        try:
                            if BUCKET_NAME in file_url:
                                # Lấy phần đường dẫn sau /{BUCKET_NAME}/
                                object_name = file_url.split(f"/{BUCKET_NAME}/")[-1]
                                minio_client.remove_object(BUCKET_NAME, object_name)
                                print(f"Deleted from MinIO: {object_name}")
                        except Exception as e:
                            print(f"MinIO delete failed for {file_url}: {e}")

                    await messages_collection.delete_one(
                        {"_id": ObjectId(message_id), "user": user}
                    )

                    await rooms_collection.update_one(
                        {"room": room},
                        {"$pull": {"messages": message_id}}
                    )

                    await broadcast({
                        "type": "delete",
                        "messageId": message_id,
                        "user": user,
                    }, sender=websocket, room=room)


            # ---- PIN MESSAGE ----
            elif msg["type"] == "pin" and user:
                action = msg.get("action", "pin")
                message_id = msg.get("messageId")

                await rooms_collection.update_one(
                    {"room": room},
                    {"$addToSet": {"pinned": msg.get("messageId")}}
                    if msg.get("action", "pin") == "pin"
                    else {"$pull": {"pinned": msg.get("messageId")}}
                )
                system_msg = {
                    "type": "system",
                    "subtype": "pin",
                    "user": user,
                    "room": room,
                    "text": f"{user} {'pinned' if action == 'pin' else 'unpinned'} a message",
                    "timestamp": datetime.utcnow(),
                }
                await messages_collection.insert_one(system_msg)
                await broadcast({
                    "type": "pin",
                    "messageId": msg.get("messageId"),
                    "user": user,
                    "action": msg.get("action", "pin"),
                }, sender=websocket, room=room)

                await broadcast({
                    "type": "system",
                    "subtype": "pin",
                    "user": user,
                    "text": system_msg["text"],
                    "room": room,
                    "timestamp": system_msg["timestamp"].isoformat(),
                }, sender=websocket, room=room)

                # ---- UNPIN MESSAGE ----
            elif msg["type"] == "unpin" and user:
                message_id = msg.get("messageId")
                await rooms_collection.update_one(
                    {"room": room},
                    {"$pull": {"pinned": message_id}}
                )
                await broadcast({
                    "type": "unpin",
                    "messageId": msg.get("messageId"),
                    "user": user,
                    "action": msg.get("action", "unpin"),
                }, sender=websocket, room=room)
            elif msg["type"] == "unpinAll" and user:
                # xóa tất cả pinned trong room
                await rooms_collection.update_one(
                    {"room": room},
                    {"$set": {"pinned": []}}
                )
                await broadcast({
                    "type": "unpinAll",
                    "user": user,
                }, sender=websocket, room=room)

            # ---- SEEN MESSAGE ----
            elif msg["type"] == "seen" and user:
                message_id = ObjectId(msg.get("messageId"))

                # cập nhật DB: thêm user vào seen_by
                await messages_collection.update_one(
                    {"_id": message_id},
                    {"$addToSet": {"seen_by": user}}
                )

                # broadcast để FE update
                await broadcast({
                    "type": "seen",
                    "messageId": str(message_id),
                    "user": user,
                }, room=room, sender=websocket)

            # ---- CALL EVENTS ----
            elif msg["type"] == "call_initiate" and user:
                await broadcast({
                    "type": "call_initiate",
                    "from": user,
                    "callType": msg.get("callType", "audio"),
                    "room": room
                }, room=room, sender=websocket)

            elif msg["type"] == "call_accept" and user:
                await broadcast({
                    "type": "call_accept",
                    "from": user,
                    "room": room
                }, room=room, sender=websocket)

            elif msg["type"] == "call_reject" and user:
                await broadcast({
                    "type": "call_reject",
                    "from": user,
                    "room": room
                }, room=room, sender=websocket)

            elif msg["type"] == "call_end" and user:
                await broadcast({
                    "type": "call_end",
                    "from": user,
                    "room": room
                }, room=room, sender=websocket)

            # ---- WebRTC SIGNALING ----
            elif msg["type"] == "webrtc_offer" and user:
                await broadcast({
                    "type": "webrtc_offer",
                    "from": user,
                    "offer": msg.get("offer"),
                    "room": room
                }, room=room, sender=websocket)

            elif msg["type"] == "webrtc_answer" and user:
                await broadcast({
                    "type": "webrtc_answer",
                    "from": user,
                    "answer": msg.get("answer"),
                    "room": room
                }, room=room, sender=websocket)

            elif msg["type"] == "webrtc_ice_candidate" and user:
                await broadcast({
                    "type": "webrtc_ice_candidate",
                    "from": user,
                    "candidate": msg.get("candidate"),
                    "room": room
                }, room=room, sender=websocket)

            # ---- SET DEFAULT EMOJI ----
            elif msg["type"] == "setDefaultEmoji" and user:
                emoji = msg.get("emoji", "👍")

                # Cập nhật defaultEmoji trong room collection
                await rooms_collection.update_one(
                    {"room": room},
                    {"$set": {f"defaultEmojis.{user}": emoji}},
                    upsert=True  # Tạo room mới nếu chưa có
                )

                # Broadcast để đồng bộ với các client khác
                await broadcast({
                    "type": "setDefaultEmoji",
                    "user": user,
                    "emoji": emoji,
                    "room": room
                }, room=room, sender=websocket)

            elif msg["type"] == "audio" and user:
                avatar_url = msg.get("avatarUrl")
                try:
                    audio_base64 = msg.get("audio")
                    if not audio_base64:
                        continue

                    audio_bytes = safe_b64decode(audio_base64)
                    file_id = str(uuid.uuid4())
                    object_name = f"{room}/{file_id}.webm"

                    minio_client.put_object(
                        BUCKET_NAME,
                        object_name,
                        io.BytesIO(audio_bytes),
                        length=len(audio_bytes),
                        content_type="audio/webm"
                    )

                    audio_url = f"{settings.MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"

                    chat_msg = {
                        "type": "audio",
                        "user": user,
                        "room": room,
                        "avatarUrl": avatar_url,
                        "audio": audio_url,
                        "timestamp": datetime.now(timezone(timedelta(hours=7))),
                    }

                    result = await messages_collection.insert_one(chat_msg)
                    chat_msg["id"] = str(result.inserted_id)
                    chat_msg["timestamp"] = chat_msg["timestamp"].isoformat()

                    await rooms_collection.update_one(
                        {"room": room},
                        {"$push": {"messages": chat_msg["id"]}}
                    )

                    await broadcast(chat_msg, room=room, sender=websocket)

                except Exception as e:
                    print("Upload audio error:", e)
            elif msg["type"] == "update_room_info" and user:
                room_name = msg.get("room")
                new_name = msg.get("newName")
                new_avatar_base64 = msg.get("newAvatar")  # base64 ảnh (nếu có)

                if not room_name:
                    continue

                update_data = {}
                change_texts = []
                current_room = await rooms_collection.find_one({"room": room_name})
                old_avatar_url = current_room.get("avatar") if current_room else None

                # Nếu có tên mới
                if new_name:
                    update_data["name"] = new_name
                    change_texts.append(f"renamed the room to '{new_name}'")

                # Nếu có ảnh mới
                if new_avatar_base64:
                    try:
                        if old_avatar_url and BUCKET_NAME in old_avatar_url:
                            try:
                                old_object_name = old_avatar_url.split(f"/{BUCKET_NAME}/")[-1]
                                minio_client.remove_object(BUCKET_NAME, old_object_name)
                                print(f"Đã xóa ảnh cũ: {old_object_name}")
                            except Exception as e:
                                print(f"Không thể xóa ảnh cũ: {e}")
                        img_bytes = safe_b64decode(new_avatar_base64)
                        file_id = str(uuid.uuid4())
                        object_name = f"rooms/{room_name}_{file_id}.png"

                        minio_client.put_object(
                            BUCKET_NAME,
                            object_name,
                            io.BytesIO(img_bytes),
                            length=len(img_bytes),
                            content_type="image/png"
                        )

                        avatar_url = f"{settings.MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"
                        update_data["avatar"] = avatar_url
                        change_texts.append("updated the room avatar")
                    except Exception as e:
                        print("Upload room avatar error:", e)
                        continue

                # Cập nhật DB
                if update_data:
                    await rooms_collection.update_one(
                        {"room": room_name},
                        {"$set": update_data}
                    )
                    # Ghi system message
                    system_text = f"{user} " + " and ".join(change_texts)
                    system_msg = {
                        "type": "system",
                        "subtype": "update_room_info",
                        "user": user,
                        "room": room_name,
                        "text": system_text,
                        "timestamp": datetime.utcnow(),
                    }
                    await messages_collection.insert_one(system_msg)

                    # Broadcast cho tất cả client trong room
                    await broadcast({
                        "type": "update_room_info",
                        "room": room_name,
                        "updatedBy": user,
                        **update_data
                    }, room=room_name, sender=websocket)

                    await broadcast({
                        "type": "system",
                        "subtype": "update_room_info",
                        "user": user,
                        "text": system_text,
                        "room": room_name,
                        "timestamp": system_msg["timestamp"].isoformat(),
                        **update_data
                    }, room=room_name, sender=websocket)

    except WebSocketDisconnect:
        username = clients.pop(websocket, None)
        if username:
            for room_name, members in rooms.items():
                if websocket in members:
                    members.pop(websocket, None)

                    # Broadcast updated online users
                    online_users = list(rooms.get(room_name, {}).values())
                    await broadcast({
                        "type": "online_users",
                        "users": online_users,
                        "count": len(online_users),
                        "room": room_name
                    }, room=room_name)



@router.get("/rooms/{room}/messages")
async def get_room_messages(room: str):
    # Lấy thông tin room
    room_doc = await rooms_collection.find_one({"room": room}) or {}
    pinned_ids = [str(pid) for pid in room_doc.get("pinned", [])]

    # Lấy toàn bộ messages trong room
    msgs_cursor = messages_collection.find({"room": room}).sort("timestamp", 1)
    msgs = []
    members = room_doc.get("members", [])
    nickname_map = room_doc.get("nicknameMap", {})

    async for m in msgs_cursor:
        msg_id_str = str(m["_id"])
        user_name = m.get("user", "Ẩn danh")

        msgs.append({
            "id": msg_id_str,
            "type": m.get("type", "chat"),
            "user": user_name,
            "avatarUrl": m.get("avatarUrl"),  # ✅ lấy trực tiếp từ DB
            "text": m.get("text") or "",
            "images": m.get("images") if isinstance(m.get("images"), list) else [],
            "audio": m.get("audio"),
            "replyTo": m.get("replyTo") if isinstance(m.get("replyTo"), dict) else None,
            "timestamp": m.get("timestamp").isoformat() if m.get("timestamp") else None,
            "reactions": m.get("reactions") if isinstance(m.get("reactions"), list) else [],
            "options": m.get("options") if isinstance(m.get("options"), list) else [],
            "pinned": str(m["_id"]) in pinned_ids,
            "edited": m.get("edited", False),
            "room": m.get("room", room),
            "readBy": m.get("seen_by", []),
        })

    room_info = {
        "room": room_doc.get("room", room),
        "name": room_doc.get("name", room_doc.get("room", room).capitalize()),
        "avatar": room_doc.get("avatar", None),
        "members": members,
        "nicknameMap": nickname_map,
    }

    default_emojis = room_doc.get("defaultEmojis", {})

    return {
        "messages": msgs,
        "pinnedMessages": pinned_ids,
        "countMembers": len(members),
        "defaultEmojis": default_emojis,
        "roomInfo": room_info,
    }

@router.get("/rooms/{room}/members")
async def get_room_members(room: str):
    doc = await rooms_collection.find_one({"room": room}, {"members": 1})
    if not doc or "members" not in doc:
        return []
    return doc["members"]

@router.post("/avatar")
async def upload_user_avatar(username: str = Form(...), file: UploadFile = File(...)):
    try:
        # Đọc file bytes
        file_bytes = await file.read()
        file_id = str(uuid.uuid4())
        object_name = f"avatars/{username}_{file_id}.png"

        # Upload lên MinIO
        minio_client.put_object(
            BUCKET_NAME,
            object_name,
            io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type="image/png"
        )

        avatar_url = f"{settings.MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"

        # Cập nhật vào MongoDB (nếu đã có thì ghi đè)
        await avatars_collection.update_one(
            {"username": username},
            {"$set": {"avatar_url": avatar_url, "updated_at": datetime.utcnow()}},
            upsert=True
        )

        return {"success": True, "avatar_url": avatar_url}

    except Exception as e:
        print("Upload user avatar error:", e)
        return {"success": False, "error": str(e)}

@router.get("/avatar/{username}")
async def get_user_avatar(username: str):
    doc = await avatars_collection.find_one({"username": username})
    if not doc:
        return {"avatar_url": None}
    return {"avatar_url": doc.get("avatar_url")}

