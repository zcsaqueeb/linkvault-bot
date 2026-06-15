"""
Database layer — Motor (async MongoDB) when MONGO_URI is set, else in-memory.
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator

logger = logging.getLogger(__name__)
MONGO_URI: str = os.environ.get("MONGO_URI", "").strip()


class Database:

    def __init__(self):
        self._backend = "memory"
        self._users: Dict[int, dict] = {}
        self._files: Dict[str, dict] = {}
        self._db = None

    # ── Connect ───────────────────────────────────────────────────────────────

    async def connect(self):
        if not MONGO_URI:
            logger.info("No MONGO_URI set — using in-memory store (data lost on restart).")
            return
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Verify connection
            await client.admin.command("ping")
            self._db = client["file_to_link_bot"]
            self._backend = "mongo"
            logger.info("MongoDB connected ✅")
        except ImportError:
            logger.warning("motor not installed — using in-memory store.")
        except Exception as e:
            logger.warning("MongoDB connection failed (%s) — using in-memory store.", e)

    # ── Users ─────────────────────────────────────────────────────────────────

    async def add_user(self, user_id: int, name: str = "", username: str = "") -> bool:
        if self._backend == "mongo":
            col = self._db["users"]
            if await col.find_one({"_id": user_id}):
                return False
            await col.insert_one({
                "_id": user_id, "name": name, "username": username,
                "joined": datetime.utcnow(), "banned": False,
            })
            return True
        if user_id not in self._users:
            self._users[user_id] = {
                "name": name, "username": username,
                "joined": datetime.utcnow(), "banned": False,
            }
            return True
        return False

    async def is_user_exist(self, user_id: int) -> bool:
        if self._backend == "mongo":
            return bool(await self._db["users"].find_one({"_id": user_id}))
        return user_id in self._users

    async def total_users_count(self) -> int:
        if self._backend == "mongo":
            return await self._db["users"].count_documents({})
        return len(self._users)

    async def get_all_users(self):
        if self._backend == "mongo":
            async for user in self._db["users"].find({}):
                yield user
        else:
            for uid, data in self._users.items():
                yield {"_id": uid, **data}

    async def ban_user(self, user_id: int) -> bool:
        if self._backend == "mongo":
            r = await self._db["users"].update_one({"_id": user_id}, {"$set": {"banned": True}})
            return r.modified_count > 0
        if user_id in self._users:
            self._users[user_id]["banned"] = True
            return True
        return False

    async def unban_user(self, user_id: int) -> bool:
        if self._backend == "mongo":
            r = await self._db["users"].update_one({"_id": user_id}, {"$set": {"banned": False}})
            return r.modified_count > 0
        if user_id in self._users:
            self._users[user_id]["banned"] = False
            return True
        return False

    async def is_banned(self, user_id: int) -> bool:
        if self._backend == "mongo":
            doc = await self._db["users"].find_one({"_id": user_id})
            return doc.get("banned", False) if doc else False
        return self._users.get(user_id, {}).get("banned", False)

    # ── Files ─────────────────────────────────────────────────────────────────

    async def save_file(self, file_id: str, meta: dict) -> None:
        if self._backend == "mongo":
            await self._db["files"].update_one(
                {"_id": file_id},
                {"$set": {**meta, "saved_at": datetime.utcnow()}},
                upsert=True,
            )
        else:
            self._files[file_id] = {**meta, "saved_at": datetime.utcnow()}

    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        if self._backend == "mongo":
            return await self._db["files"].find_one({"_id": file_id})
        return self._files.get(file_id)

    async def total_files_count(self) -> int:
        if self._backend == "mongo":
            return await self._db["files"].count_documents({})
        return len(self._files)

    async def delete_file(self, file_id: str) -> bool:
        if self._backend == "mongo":
            r = await self._db["files"].delete_one({"_id": file_id})
            return r.deleted_count > 0
        return bool(self._files.pop(file_id, None))
