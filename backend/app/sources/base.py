"""ProductSource Abstract Base Class.

Provides data-source abstraction for product information retrieval in EviBite AI.
This enables future supermarket catalog databases to sit alongside or replace
Open Food Facts without modifying agent contracts.
"""

from abc import ABC, abstractmethod
from typing import Any
from backend.app.agents.agent_stubs import EvidenceObject


class ProductSource(ABC):
    """Abstract interface for product data sources."""

    @abstractmethod
    def get_by_barcode(self, barcode: str) -> EvidenceObject | None:
        """Lookup an exact product record by barcode.
        
        Returns EvidenceObject if found, None otherwise.
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        category: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[EvidenceObject]:
        """Search products by free text query, brand, or category.
        
        Returns a list of candidate EvidenceObjects.
        """
        pass
