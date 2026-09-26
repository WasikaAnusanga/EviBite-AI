"""MongoDB Chat Repository for EviBite AI.

Persists user chat sessions and messages in MongoDB collection `evibite_db.chat_sessions`.
Allows each user to view their saved chat history and resume conversations seamlessly.
"""

import os
import datetime
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb+srv://wasikaanusanga12_db_user:fs2KRDDRw8hBfjYv@cluster0.6rqhrfb.mongodb.net/evibite_db?retryWrites=true&w=majority"


class ChatRepository:
    def __init__(self):
        self.db = None
        self.collection = None
        self._memory_chats: Dict[str, Dict[str, Any]] = {}
        self._connect_db()

    def _connect_db(self):
        """Initialize MongoDB client with SSL fallback options."""
        try:
            from backend.app.db.product_repository import _configure_dns_resolver
            _configure_dns_resolver()
            import pymongo
            import certifi

            client = pymongo.MongoClient(
                MONGODB_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=4000,
            )
            client.admin.command("ping")
            
            db_name = "evibite_db"
            self.db = client[db_name]
            self.collection = self.db["chat_sessions"]
            # Ensure indexes for user_id and session id lookup
            self.collection.create_index("id", unique=True)
            self.collection.create_index("user_id")
            self.collection.create_index("updated_at")
            logger.info("Successfully connected to MongoDB Atlas for Chat Storage!")
        except Exception as e:
            logger.warning(f"MongoDB Chat storage notice: {e}. Operating in local memory fallback.")

    def save_or_update_session(
        self,
        session_id: str,
        user_id: Optional[str],
        title: str,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Save or update a chat session in MongoDB."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        session_doc = {
            "id": session_id,
            "user_id": user_id,
            "title": title[:40] if title else "New Chat",
            "messages": messages,
            "updated_at": now_iso,
        }

        if self.collection is not None:
            try:
                self.collection.update_one(
                    {"id": session_id},
                    {
                        "$set": session_doc,
                        "$setOnInsert": {"created_at": now_iso},
                    },
                    upsert=True,
                )
            except Exception as e:
                logger.error(f"MongoDB error saving chat session '{session_id}': {e}")

        # Keep memory fallback updated
        self._memory_chats[session_id] = session_doc
        return session_doc

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chat sessions for a specific user ordered by updated_at descending."""
        sessions = []
        if self.collection is not None:
            try:
                cursor = self.collection.find({"user_id": user_id}).sort("updated_at", -1)
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    sessions.append(doc)
                return sessions
            except Exception as e:
                logger.error(f"MongoDB error fetching user sessions: {e}")

        # Fallback search
        for sess in self._memory_chats.values():
            if sess.get("user_id") == user_id:
                sessions.append(sess)
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

    def get_session_by_id(self, session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a single chat session by session_id."""
        if self.collection is not None:
            try:
                query = {"id": session_id}
                if user_id:
                    query["user_id"] = user_id
                doc = self.collection.find_one(query)
                if doc:
                    doc["_id"] = str(doc["_id"])
                    return doc
                return None
            except Exception as e:
                logger.error(f"MongoDB error fetching session '{session_id}': {e}")

        sess = self._memory_chats.get(session_id)
        if sess and (user_id is None or sess.get("user_id") == user_id):
            return sess
        return None

    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a chat session from MongoDB."""
        if self.collection is not None:
            try:
                query = {"id": session_id}
                if user_id:
                    query["user_id"] = user_id
                res = self.collection.delete_one(query)
                return res.deleted_count > 0
            except Exception as e:
                logger.error(f"MongoDB error deleting session '{session_id}': {e}")

        if session_id in self._memory_chats:
            del self._memory_chats[session_id]
            return True
        return False


# Singleton chat repository instance
chat_repo = ChatRepository()
