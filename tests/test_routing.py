from backend.app.models.triage import Intent, RouteAgent
from backend.app.orchestration.routing import build_routing


def test_allergen_requires_analysis():
    route = build_routing(Intent.ALLERGEN_QUERY)
    assert route.analysis_required is True
    assert RouteAgent.ANALYSIS in route.required_agents


def test_product_search_skips_analysis():
    route = build_routing(Intent.PRODUCT_SEARCH)
    assert route.analysis_required is False
    assert route.required_agents == [RouteAgent.RETRIEVAL, RouteAgent.RESPONSE]
