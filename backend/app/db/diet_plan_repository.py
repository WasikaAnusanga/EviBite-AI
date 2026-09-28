"""MongoDB Diet Plan Repository for EviBite AI.

Persists user personalized diet plans, macronutrient targets, grounded meal structures,
and supermarket grocery lists in MongoDB collection `evibite_db.saved_diet_plans`.
Allows users to save, review, print, and manage their nutrition blueprints across sessions.
Includes in-memory fallback storage for resilient offline operation.
"""

import os
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb+srv://wasikaanusanga12_db_user:fs2KRDDRw8hBfjYv@cluster0.6rqhrfb.mongodb.net/evibite_db?retryWrites=true&w=majority"


class DietPlanRepository:
    def __init__(self):
        self.db = None
        self.collection = None
        self._memory_plans: Dict[str, Dict[str, Any]] = {}
        self._last_fail_time = 0.0
        self._connect_db()

    def _connect_db(self):
        """Initialize MongoDB client with fast timeout and SSL configuration."""
        if time.time() - getattr(self, "_last_fail_time", 0.0) < 120.0:
            return

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
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=3000,
            )
            client.admin.command("ping")

            db_name = "evibite_db"
            self.db = client[db_name]
            self.collection = self.db["saved_diet_plans"]

            # Ensure optimal indexes for fast user retrieval
            self.collection.create_index("id", unique=True)
            self.collection.create_index("user_id")
            self.collection.create_index("created_at")
            logger.info("Successfully connected to MongoDB Atlas for Saved Diet Plans!")
        except Exception as e:
            self._last_fail_time = time.time()
            logger.warning(f"MongoDB Saved Diet Plans connection notice: {e}. Operating in memory fallback.")

    def _ensure_connected(self) -> bool:
        if self.collection is None:
            self._connect_db()
        return self.collection is not None

    def save_plan(
        self,
        user_id: str,
        plan_data: Dict[str, Any],
        profile_data: Optional[Dict[str, Any]] = None,
        plan_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save or update a generated diet plan for a specific user."""
        now_iso = datetime.now(timezone.utc).isoformat()
        plan_id = plan_data.get("trace_id") or plan_data.get("id") or f"plan_{uuid.uuid4().hex[:10]}"

        # Derive a human-readable title if not explicitly provided
        derived_title = plan_name
        if not derived_title:
            user_goal = plan_data.get("user_goal") or "Nutrition"
            user_country = plan_data.get("user_country") or "Global"
            derived_title = f"{user_country} {user_goal} Blueprint"

        doc = {
            "id": plan_id,
            "user_id": str(user_id),
            "title": derived_title,
            "user_goal": plan_data.get("user_goal"),
            "user_diet": plan_data.get("user_diet"),
            "user_country": plan_data.get("user_country") or "United States",
            "daily_targets": plan_data.get("daily_targets"),
            "meals": plan_data.get("meals", []),
            "shopping_list": plan_data.get("shopping_list", []),
            "explanation": plan_data.get("explanation", ""),
            "safety_summary": plan_data.get("safety_summary", ""),
            "profile": profile_data or {},
            "created_at": plan_data.get("timestamp") or now_iso,
            "updated_at": now_iso,
        }

        # Save to memory fallback cache
        self._memory_plans[plan_id] = doc

        # Save to MongoDB Atlas
        if self._ensure_connected() and self.collection is not None:
            try:
                self.collection.update_one(
                    {"id": plan_id},
                    {"$set": doc},
                    upsert=True,
                )
            except Exception as e:
                logger.warning(f"Failed to upsert saved diet plan to MongoDB: {e}")

        return doc

    def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all saved diet plans for a user, sorted newest first."""
        user_str = str(user_id)
        plans: List[Dict[str, Any]] = []

        if self._ensure_connected() and self.collection is not None:
            try:
                cursor = self.collection.find({"user_id": user_str}).sort("created_at", -1)
                for item in cursor:
                    item.pop("_id", None)
                    plans.append(item)
                return plans
            except Exception as e:
                logger.warning(f"Failed to fetch user diet plans from MongoDB: {e}")

        # Fallback to in-memory store
        for p in self._memory_plans.values():
            if str(p.get("user_id")) == user_str:
                plans.append(p)

        plans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return plans

    def get_plan_by_id(self, plan_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Look up a specific diet plan by plan_id."""
        if self._ensure_connected() and self.collection is not None:
            try:
                query: Dict[str, Any] = {"id": plan_id}
                if user_id:
                    query["user_id"] = str(user_id)
                doc = self.collection.find_one(query)
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                logger.warning(f"Failed to find diet plan in MongoDB: {e}")

        # Fallback to in-memory store
        doc = self._memory_plans.get(plan_id)
        if doc and (user_id is None or str(doc.get("user_id")) == str(user_id)):
            return doc

        return None

    def delete_plan(self, plan_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a saved diet plan by plan_id."""
        success = False
        if self._ensure_connected() and self.collection is not None:
            try:
                query: Dict[str, Any] = {"id": plan_id}
                if user_id:
                    query["user_id"] = str(user_id)
                res = self.collection.delete_one(query)
                success = res.deleted_count > 0
            except Exception as e:
                logger.warning(f"Failed to delete diet plan from MongoDB: {e}")

        # Remove from in-memory fallback
        if plan_id in self._memory_plans:
            doc = self._memory_plans[plan_id]
            if user_id is None or str(doc.get("user_id")) == str(user_id):
                del self._memory_plans[plan_id]
                success = True

        return success


# Global singleton instance
diet_plan_repo = DietPlanRepository()
