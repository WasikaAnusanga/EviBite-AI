"""Commercialization Strategy API Router for EviBite AI.
Exposes business model tiers and pricing structure for live presentation and API consumers.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/commercialization", tags=["commercialization"])


class PricingTier(BaseModel):
    name: str
    target_audience: str
    price: str
    features: list[str]


class BusinessModelResponse(BaseModel):
    system_name: str = "EviBite AI"
    value_proposition: str = "Multi-Agent Supermarket Product Intelligence Platform"
    b2c_subscriptions: list[PricingTier] = Field(default_factory=list)
    b2b_enterprise_api: list[PricingTier] = Field(default_factory=list)


@router.get("/tiers", response_model=BusinessModelResponse)
def get_commercialization_tiers() -> BusinessModelResponse:
    """Returns the commercialization pricing tiers and business model breakdown."""
    b2c_tiers = [
        PricingTier(
            name="Free Tier",
            target_audience="Casual Shoppers",
            price="$0 / month",
            features=[
                "10 product scans or queries per day",
                "Basic allergen warning flags",
                "Nutri-Score & Eco-Score display",
            ],
        ),
        PricingTier(
            name="Shopper Premium",
            target_audience="Allergy & Fitness Shoppers",
            price="$4.99 / month (or $44.99 / year)",
            features=[
                "Unlimited barcode & natural language queries",
                "Family Allergy Profiles (up to 5 profiles)",
                "Custom nutrient threshold goals (low-sugar, high-protein)",
                "Instant healthier alternative recommendations",
            ],
        ),
    ]

    b2b_tiers = [
        PricingTier(
            name="API Starter",
            target_audience="Independent Grocers & Apps",
            price="$299 / month",
            features=[
                "Up to 50,000 API calls / month",
                "REST API access for product search & allergen checking",
                "Standard support",
            ],
        ),
        PricingTier(
            name="Retail Enterprise",
            target_audience="National Supermarket Chains",
            price="$1,499 / month",
            features=[
                "Up to 500,000 API calls / month",
                "Custom Database Adapter (Live branch stock, price, & aisle API)",
                "Smart Shopping Cart & In-Store Kiosk SDK",
                "99.9% uptime SLA & dedicated technical account manager",
            ],
        ),
    ]

    return BusinessModelResponse(
        b2c_subscriptions=b2c_tiers,
        b2b_enterprise_api=b2b_tiers,
    )
