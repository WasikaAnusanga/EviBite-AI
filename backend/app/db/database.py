import os
from typing import Any
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "evibite_db")

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    client = get_mongo_client()
    return client[DB_NAME]


def init_db():
    """Ensure indexes exist for collections."""
    db = get_db()
    # Create unique index on user email
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.chat_sessions.create_index([("user_id", ASCENDING)])
    db.chat_messages.create_index([("session_id", ASCENDING)])
    db.chat_messages.create_index([("user_id", ASCENDING)])

