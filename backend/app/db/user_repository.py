"""MongoDB User Repository for EviBite AI Auth System.

Handles database connection to MongoDB Atlas / local MongoDB with certificate fallback,
and provides user CRUD operations (register, login verification, profile lookup).
"""

import os
import uuid
import datetime
import logging
import bcrypt
import jwt
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET") or "evibite-super-secret-jwt-key-2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# Check MongoDB connection string from environment
MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb+srv://wasikaanusanga12_db_user:fs2KRDDRw8hBfjYv@cluster0.6rqhrfb.mongodb.net/evibite_db?retryWrites=true&w=majority"


class UserRepository:
    def __init__(self):
        self.db = None
        self.collection = None
        self._memory_users: Dict[str, Dict[str, Any]] = {}
        self._connect_db()

    def _connect_db(self):
        """Initialize MongoDB client with SSL fallback options."""
        try:
            from backend.app.db.product_repository import _configure_dns_resolver
            _configure_dns_resolver()
            import pymongo
            import certifi

            # Attempt connection with certifi & tls settings
            client = pymongo.MongoClient(
                MONGODB_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=4000,
            )
            # Ping database to confirm connection
            client.admin.command("ping")
            
            # Select database
            db_name = "evibite_db"
            self.db = client[db_name]
            self.collection = self.db["users"]
            # Ensure unique index on email
            self.collection.create_index("email", unique=True)
            logger.info("Successfully connected to MongoDB Atlas!")
        except Exception as e:
            logger.warning(f"MongoDB connection notice: {e}. Operating with persistent local user repository.")

    def hash_password(self, password: str) -> str:
        """Hash plain text password with bcrypt salt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify plain text password against bcrypt hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_token(self, user_id: str, email: str, name: str) -> str:
        """Generate JWT authentication token."""
        payload = {
            "sub": user_id,
            "email": email,
            "name": name,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.datetime.now(datetime.timezone.utc),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT authentication token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email address."""
        email_clean = email.lower().strip()
        if self.collection is not None:
            try:
                user_doc = self.collection.find_one({"email": email_clean})
                if user_doc:
                    user_doc["_id"] = str(user_doc["_id"])
                    return user_doc
                return None  # Direct database source of truth
            except Exception as e:
                logger.error(f"MongoDB lookup error: {e}")
        
        # Memory fallback search only if DB connection is offline
        return self._memory_users.get(email_clean)

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by user ID."""
        if self.collection is not None:
            try:
                user_doc = self.collection.find_one({"id": user_id})
                if user_doc:
                    user_doc["_id"] = str(user_doc["_id"])
                    return user_doc
                return None  # Direct database source of truth
            except Exception as e:
                logger.error(f"MongoDB lookup error: {e}")

        # Memory fallback search only if DB connection is offline
        for user in self._memory_users.values():
            if user.get("id") == user_id:
                return user
        return None

    def create_user(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user in MongoDB securely."""
        email_clean = email.lower().strip()
        
        if self.find_by_email(email_clean):
            raise ValueError("User with this email already exists")

        hashed_pw = self.hash_password(password)
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        user_doc = {
            "id": user_id,
            "name": name.strip(),
            "email": email_clean,
            "password_hash": hashed_pw,
            "plan_tier": "free",
            "daily_msg_count": 0,
            "last_msg_date": "",
            "created_at": created_at,
        }

        if self.collection is not None:
            try:
                from pymongo.errors import DuplicateKeyError
                self.collection.insert_one(user_doc.copy())
            except DuplicateKeyError:
                raise ValueError("User with this email already exists")
            except Exception as e:
                logger.error(f"MongoDB insert user error: {e}")
                raise ValueError(f"Failed to create user in database: {str(e)}")
        else:
            self._memory_users[email_clean] = user_doc

        return {
            "id": user_id,
            "name": user_doc["name"],
            "email": user_doc["email"],
            "plan_tier": "free",
            "daily_msg_count": 0,
            "created_at": created_at,
        }

    def check_and_increment_daily_chat(self, user_id: str) -> tuple[bool, int, int]:
        """Check if user can send a chat message under their current tier.
        Returns tuple: (is_allowed, current_count, remaining_chats)
        """
        user = self.find_by_id(user_id)
        if not user:
            # Guest user - allow under free plan limits (10 msgs/day)
            user = {
                "id": "guest_user",
                "plan_tier": "free",
                "daily_msg_count": 0,
                "last_msg_date": "",
            }

        plan_tier = user.get("plan_tier", "free")
        
        # Pro & Ultimate have unlimited chats
        if plan_tier in {"pro", "ultimate"}:
            return True, 0, 9999

        # Free tier: 10 daily chats limit
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        last_date = user.get("last_msg_date", "")
        current_count = user.get("daily_msg_count", 0)

        # Reset count if it's a new calendar day
        if last_date != today_str:
            current_count = 0

        FREE_LIMIT = 10
        if current_count >= FREE_LIMIT:
            return False, current_count, 0

        # Increment count
        new_count = current_count + 1
        remaining = FREE_LIMIT - new_count

        # Update in DB / memory
        if self.collection is not None and user.get("id") != "guest_user":
            try:
                self.collection.update_one(
                    {"id": user["id"]},
                    {"$set": {"daily_msg_count": new_count, "last_msg_date": today_str}}
                )
            except Exception as e:
                logger.error(f"Error updating daily chat count: {e}")

        if user.get("email") and user["email"] in self._memory_users:
            self._memory_users[user["email"]]["daily_msg_count"] = new_count
            self._memory_users[user["email"]]["last_msg_date"] = today_str

        return True, new_count, remaining

    def update_user_tier(self, user_id: str, plan_tier: str) -> Dict[str, Any]:
        """Update user subscription plan tier (free, pro, ultimate)."""
        valid_tiers = {"free", "pro", "ultimate"}
        clean_tier = plan_tier.lower().strip()
        if clean_tier not in valid_tiers:
            raise ValueError(f"Invalid plan tier '{plan_tier}'. Must be one of {valid_tiers}")

        if self.collection is not None:
            try:
                self.collection.update_one(
                    {"id": user_id},
                    {"$set": {"plan_tier": clean_tier}}
                )
            except Exception as e:
                logger.error(f"Error updating user tier: {e}")

        user = self.find_by_id(user_id)
        if user:
            user["plan_tier"] = clean_tier
            if user.get("email") and user["email"] in self._memory_users:
                self._memory_users[user["email"]]["plan_tier"] = clean_tier
            return user
        
        return {"id": user_id, "plan_tier": clean_tier}


# Singleton instance
user_repo = UserRepository()
