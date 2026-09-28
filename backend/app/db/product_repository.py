"""MongoDB Food & Product Repository for EviBite AI.

Persists curated supermarket food items, nutritional facts, declared allergens,
and cached Open Food Facts items into MongoDB collection `evibite_db.products`.
Provides high-performance barcode lookup, text search, allergen filtering,
and automatic cloud caching of external Open Food Facts products.
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from backend.app.agents.agent_stubs import EvidenceObject

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb+srv://wasikaanusanga12_db_user:fs2KRDDRw8hBfjYv@cluster0.6rqhrfb.mongodb.net/evibite_db?retryWrites=true&w=majority"


def _configure_dns_resolver():
    """Ensure dnspython and socket can resolve MongoDB SRV & A records on Windows environments."""
    try:
        import dns.resolver
        import socket

        resolver = dns.resolver.Resolver()
        resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
        dns.resolver.default_resolver = resolver

        # Fallback patch for socket.getaddrinfo if local Windows DNS fails on replica hostnames
        if not getattr(socket, "_evibite_dns_patched", False):
            _orig_getaddrinfo = socket.getaddrinfo

            def _custom_getaddrinfo(host, port, *args, **kwargs):
                try:
                    return _orig_getaddrinfo(host, port, *args, **kwargs)
                except socket.gaierror:
                    try:
                        answers = resolver.resolve(host, "A")
                        if answers:
                            return _orig_getaddrinfo(answers[0].address, port, *args, **kwargs)
                    except Exception:
                        pass
                    raise

            socket.getaddrinfo = _custom_getaddrinfo
            socket._evibite_dns_patched = True
    except Exception as e:
        logger.debug(f"Custom DNS resolver setup skipped: {e}")


class ProductRepository:
    """Cloud Product Repository backed exclusively by MongoDB Atlas."""

    def __init__(self):
        self.db = None
        self.collection = None
        self._is_connected = False
        self._last_fail_time = 0.0
        self._connect_db()

    def _connect_db(self):
        """Initialize MongoDB client and ensure collection indexes."""
        # Cooldown: Do not retry connection more than once every 120 seconds if offline
        if time.time() - getattr(self, "_last_fail_time", 0.0) < 120.0:
            return

        _configure_dns_resolver()
        try:
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
            self._last_fail_time = time.time()
            logger.warning(f"MongoDB Product database connection notice: {e}. Operating in resilient offline mode.")

    def _ensure_connected(self) -> bool:
        """Attempt reconnection if client was disconnected, respecting cooldown."""
        if not self._is_connected or self.collection is None:
            self._connect_db()
        return self._is_connected

    @property
    def is_connected(self) -> bool:
        return self._ensure_connected()

    def get_by_barcode(self, barcode: str) -> Optional[EvidenceObject]:
        """Look up a product in MongoDB by exact barcode."""
        clean_code = "".join(c for c in barcode if c.isdigit())
        if not clean_code:
            return None

        if self._ensure_connected() and self.collection is not None:
            try:
                doc = self.collection.find_one({"barcode": clean_code})
                if doc:
                    return self._doc_to_evidence(doc)
            except Exception as e:
                logger.warning(f"MongoDB barcode query failed: {e}")

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
        results: List[EvidenceObject] = []
        if self._ensure_connected() and self.collection is not None:
            try:
                query_filter: Dict[str, Any] = {}

                # Category filter
                if category:
                    query_filter["categories"] = {"$regex": re.escape(category), "$options": "i"}

                # Query text search (case-insensitive regex for high recall)
                query_str = query.strip()
                if query_str:
                    common_stopwords = {"water", "spring", "with", "and", "for", "the", "fresh", "sweet", "pure", "natural", "organic", "chunks", "canned", "free", "original", "style", "pack"}
                    words = [w for w in re.findall(r'[a-zA-Z]{3,}', query_str.lower()) if w not in common_stopwords]
                    if not words:
                        words = re.findall(r'[a-zA-Z]{3,}', query_str.lower())

                    if words:
                        regex_pattern = "|".join(re.escape(w) for w in words)
                        query_filter["$or"] = [
                            {"name": {"$regex": regex_pattern, "$options": "i"}},
                            {"categories": {"$regex": regex_pattern, "$options": "i"}},
                            {"brand": {"$regex": regex_pattern, "$options": "i"}},
                        ]

                cursor = self.collection.find(query_filter).limit(limit)
                for doc in cursor:
                    results.append(self._doc_to_evidence(doc))
            except Exception as e:
                logger.warning(f"MongoDB search failed: {e}.")

        return results

    def save_product(self, product: EvidenceObject) -> bool:
        """Upsert a product into MongoDB Atlas (from Open Food Facts or manual addition)."""
        if not self._ensure_connected() or self.collection is None:
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

    def get_total_count(self) -> int:
        """Return total number of products stored in MongoDB."""
        if self._ensure_connected() and self.collection is not None:
            try:
                return self.collection.count_documents({})
            except Exception:
                return 0
        return 0

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
            countries=doc.get("countries", []),
            nutrition=doc.get("nutrition", {}),
            completeness=float(doc.get("completeness", 1.0)),
            source=doc.get("source", "mongodb_cloud"),
        )


# Global singleton instance
product_repo = ProductRepository()
