"""MongoDB Food & Product Repository for EviBite AI.

Persists curated supermarket food items, nutritional facts, declared allergens,
and cached Open Food Facts items into MongoDB collection `evibite_db.products`.
Provides high-performance barcode lookup, text search, allergen filtering,
and automatic cloud caching of external Open Food Facts products.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from backend.app.agents.agent_stubs import EvidenceObject
from backend.app.db.food_database import FOOD_DATABASE, search_local_database

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb+srv://wasikaanusanga12_db_user:fs2KRDDRw8hBfjYv@cluster0.6rqhrfb.mongodb.net/evibite_db?retryWrites=true&w=majority"


def _configure_dns_resolver():
    """Ensure dnspython can resolve MongoDB SRV records on Windows environments."""
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
        dns.resolver.default_resolver = resolver
    except Exception as e:
        logger.debug(f"Custom DNS resolver setup skipped: {e}")


class ProductRepository:
    """Cloud Product Repository backed by MongoDB Atlas with in-memory fallback."""

    def __init__(self):
        self.db = None
        self.collection = None
        self._is_connected = False
        self._connect_db()

    def _connect_db(self):
        """Initialize MongoDB client and ensure collection indexes."""
        _configure_dns_resolver()
        try:
            import pymongo
            import certifi

            client = pymongo.MongoClient(
                MONGODB_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=15000,
            )
            client.admin.command("ping")

            db_name = "evibite_db"
            self.db = client[db_name]
            self.collection = self.db["products"]

            # Ensure optimal indexes for fast queries
            self.collection.create_index("product_id", unique=True)
            self.collection.create_index("barcode", sparse=True)
            self.collection.create_index("categories")
            self.collection.create_index("allergens")
            
            # Full-text search index across name, brand, categories, and ingredients
            try:
                self.collection.create_index(
                    [
                        ("name", pymongo.TEXT),
                        ("brand", pymongo.TEXT),
                        ("categories", pymongo.TEXT),
                        ("ingredients_text", pymongo.TEXT),
                    ],
                    weights={"name": 10, "brand": 5, "categories": 3, "ingredients_text": 1},
                    name="product_text_index",
                )
            except Exception:
                pass  # Index may already exist with slightly different parameters

            self._is_connected = True
            logger.info("Successfully connected to MongoDB Atlas for Product Database!")
        except Exception as e:
            self._is_connected = False
            logger.warning(
                f"MongoDB Product database connection notice: {e}. "
                "Operating with in-memory food database fallback."
            )

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def get_by_barcode(self, barcode: str) -> Optional[EvidenceObject]:
        """Look up a product in MongoDB by exact barcode."""
        clean_code = "".join(c for c in barcode if c.isdigit())
        if not clean_code:
            return None

        if self._is_connected and self.collection is not None:
            try:
                doc = self.collection.find_one({"barcode": clean_code})
                if doc:
                    return self._doc_to_evidence(doc)
            except Exception as e:
                logger.warning(f"MongoDB barcode query failed: {e}")

        # Fallback to local in-memory database
        for item in FOOD_DATABASE:
            if item.barcode == clean_code:
                return item
        return None

    def search(
        self,
        query: str = "",
        category: Optional[str] = None,
        allergens: Optional[List[str]] = None,
        dietary: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[EvidenceObject]:
        """Search products in MongoDB using regex / text match + category & allergen filters."""
        if self._is_connected and self.collection is not None:
            try:
                results: List[EvidenceObject] = []
                query_filter: Dict[str, Any] = {}

                # Category filter
                if category:
                    query_filter["categories"] = {"$regex": re.escape(category), "$options": "i"}

                # Query text search (case-insensitive regex for high recall)
                query_str = query.strip()
                if query_str:
                    words = [w for w in query_str.lower().split() if len(w) > 2]
                    if words:
                        # Regex match in name or brand
                        regex_pattern = "|".join(re.escape(w) for w in words)
                        query_filter["$or"] = [
                            {"name": {"$regex": regex_pattern, "$options": "i"}},
                            {"brand": {"$regex": regex_pattern, "$options": "i"}},
                            {"categories": {"$regex": regex_pattern, "$options": "i"}},
                            {"ingredients_text": {"$regex": regex_pattern, "$options": "i"}},
                        ]

                cursor = self.collection.find(query_filter).limit(limit)
                for doc in cursor:
                    results.append(self._doc_to_evidence(doc))

                if results:
                    return results
            except Exception as e:
                logger.warning(f"MongoDB search failed: {e}. Falling back to in-memory database.")

        # Fallback to curated in-memory search
        return search_local_database(
            query=query,
            category=category,
            allergens=allergens,
            dietary=dietary,
            limit=limit,
        )

    def save_product(self, product: EvidenceObject) -> bool:
        """Upsert a product into MongoDB Atlas (from local seed or Open Food Facts)."""
        if not self._is_connected or self.collection is None:
            return False

        try:
            doc = product.model_dump()
            filter_query = {"product_id": product.product_id}
            if product.barcode:
                filter_query = {"$or": [{"product_id": product.product_id}, {"barcode": product.barcode}]}

            self.collection.update_one(filter_query, {"$set": doc}, upsert=True)
            return True
        except Exception as e:
            logger.warning(f"Failed to upsert product '{product.name}' into MongoDB: {e}")
            return False

    def seed_from_local_database(self) -> int:
        """Seed all curated items from in-memory FOOD_DATABASE into MongoDB Atlas."""
        if not self._is_connected or self.collection is None:
            logger.warning("Cannot seed: MongoDB not connected.")
            return 0

        inserted_or_updated = 0
        for item in FOOD_DATABASE:
            success = self.save_product(item)
            if success:
                inserted_or_updated += 1

        logger.info(f"Successfully seeded {inserted_or_updated} products into MongoDB Atlas.")
        return inserted_or_updated

    def get_total_count(self) -> int:
        """Return total number of products stored in MongoDB."""
        if self._is_connected and self.collection is not None:
            try:
                return self.collection.count_documents({})
            except Exception:
                return 0
        return len(FOOD_DATABASE)

    @staticmethod
    def _doc_to_evidence(doc: Dict[str, Any]) -> EvidenceObject:
        """Convert MongoDB document to an EvidenceObject."""
        return EvidenceObject(
            product_id=str(doc.get("product_id") or doc.get("_id")),
            name=doc.get("name", "Unknown Product"),
            brand=doc.get("brand"),
            barcode=doc.get("barcode"),
            categories=doc.get("categories", []),
            ingredients_text=doc.get("ingredients_text"),
            allergens=doc.get("allergens", []),
            nutrition=doc.get("nutrition", {}),
            completeness=float(doc.get("completeness", 1.0)),
            source=doc.get("source", "mongodb_cloud"),
        )


# Global singleton instance
product_repo = ProductRepository()
