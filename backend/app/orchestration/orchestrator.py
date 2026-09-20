"""Orchestrator Engine for EviBite AI (Owned by Member 1).

Manages conditional multi-agent routing, message envelope propagation,
trace ID tracking, execution step timing, and error resilience across
Triage, Retrieval, Analysis, and Response agents.
"""

import time
import logging
from typing import Any

from backend.app.agents.agent_stubs import (
    AnalysisRequest,
    AnalysisResponse,
    RetrievalRequest,
    ResponseRequest,
    stub_response_service,
)
from backend.app.agents.nutrition_allergen.service import analysis_service
from backend.app.agents.retrieval.service import retrieval_service
from backend.app.agents.triage.service import triage_message
from backend.app.agents.recommendation_response.service import response_service
from backend.app.models.messages import ChatRequest, ChatResponse, ExecutionStep
from backend.app.models.triage import RouteAgent, TriageRequest, TriageStatus

logger = logging.getLogger(__name__)


def run_orchestration(request: ChatRequest) -> ChatResponse:
    user_query = request.message.strip()
    execution_steps: list[ExecutionStep] = []
    execution_path: list[str] = []

    # Step 1: Execute Agent 1 (Triage & Routing)
    start_triage = time.perf_counter()
    triage_req = TriageRequest(
        message=user_query,
        session_id=request.session_id,
        previous_product=request.previous_product,
    )
    triage_output = triage_message(triage_req)
    triage_ms = round((time.perf_counter() - start_triage) * 1000)

    trace_id = triage_output.trace_id

    execution_path.append("triage")
    execution_steps.append(
        ExecutionStep(
            agent="triage",
            action=f"intent_extraction:{triage_output.primary_intent.value}",
            status=triage_output.triage_status.value,
            duration_ms=triage_ms,
            summary=f"Intent: {triage_output.primary_intent.value}",
        )
    )

    # Early exit 1: Clarification required
    if triage_output.triage_status == TriageStatus.CLARIFICATION_REQUIRED:
        question = (
            triage_output.clarification.question
            or "Could you please specify which product you would like me to check?"
        )
        return ChatResponse(
            trace_id=trace_id,
            session_id=request.session_id,
            query=user_query,
            execution_path=execution_path,
            execution_steps=execution_steps,
            triage_output=triage_output.model_dump(),
            final_response=question,
        )

    # Early exit 2: Unsupported query
    if triage_output.triage_status == TriageStatus.UNSUPPORTED:
        execution_path.append("response")
        start_resp = time.perf_counter()
        resp_stub = stub_response_service(
            ResponseRequest(
                trace_id=trace_id,
                query=user_query,
                intent=triage_output.primary_intent.value,
                triage_status=triage_output.triage_status.value,
            )
        )
        resp_ms = round((time.perf_counter() - start_resp) * 1000)
        execution_steps.append(
            ExecutionStep(
                agent="response",
                action="unsupported_query_handling",
                status="OK",
                duration_ms=resp_ms,
                summary="Handled unsupported query",
            )
        )
        return ChatResponse(
            trace_id=trace_id,
            session_id=request.session_id,
            query=user_query,
            execution_path=execution_path,
            execution_steps=execution_steps,
            triage_output=triage_output.model_dump(),
            final_response=resp_stub.answer,
        )

    # Early exit 3: No retrieval required (Greeting / Out of Domain)
    required_agents = triage_output.routing.required_agents or []
    if RouteAgent.RETRIEVAL not in required_agents:
        execution_path.append("response")
        start_resp = time.perf_counter()
        response_req = ResponseRequest(
            trace_id=trace_id,
            query=user_query,
            intent=triage_output.primary_intent.value,
            triage_status=triage_output.triage_status.value,
            evidence=[],
            analysis=None,
        )
        response_res = response_service(response_req)
        resp_ms = round((time.perf_counter() - start_resp) * 1000)
        execution_steps.append(
            ExecutionStep(
                agent="response",
                action="conversational_response_generation",
                status="OK",
                duration_ms=resp_ms,
                summary="Generated conversational response",
            )
        )
        return ChatResponse(
            trace_id=trace_id,
            session_id=request.session_id,
            query=user_query,
            execution_path=execution_path,
            execution_steps=execution_steps,
            triage_output=triage_output.model_dump(),
            final_response=response_res.answer,
        )

    # Step 2: Execute Agent 2 (Product Information Retrieval)
    execution_path.append("retrieval")
    start_ret = time.perf_counter()
    retrieval_req = RetrievalRequest(
        trace_id=trace_id,
        query=user_query,
        intent=triage_output.primary_intent.value,
        products=[p.model_dump() for p in triage_output.products],
        category=triage_output.category,
        requested_fields=triage_output.requested_fields,
        user_id=getattr(request, "user_id", None),
        comparison_targets=triage_output.comparison_targets,
        triage_context=triage_output.model_dump(),
    )
    retrieval_res = retrieval_service(retrieval_req)
    ret_ms = round((time.perf_counter() - start_ret) * 1000)

    num_candidates = len(retrieval_res.candidates)
    sources_summary = ", ".join(retrieval_res.searched_sources)
    execution_steps.append(
        ExecutionStep(
            agent="retrieval",
            action=f"candidate_retrieval:{num_candidates} candidates",
            status=retrieval_res.status,
            duration_ms=ret_ms,
            summary=f"Retrieved {num_candidates} evidence objects via {sources_summary}",
        )
    )

    # Step 3: Execute Agent 3 (Nutrition & Allergen Analysis) if required
    analysis_res: AnalysisResponse | None = None
    if (
        triage_output.routing.analysis_required
        or RouteAgent.ANALYSIS in required_agents
    ):
        execution_path.append("analysis")
        start_ana = time.perf_counter()
        analysis_req = AnalysisRequest(
            trace_id=trace_id,
            primary_intent=triage_output.primary_intent.value,
            allergens=triage_output.allergens,
            nutrients=triage_output.nutrients,
            dietary_requirements=triage_output.dietary_requirements,
            nutrient_constraints=triage_output.nutrient_constraints,
            constraints=triage_output.constraints,
            evidence=retrieval_res.candidates,
            original_query=user_query,
        )

        try:
            analysis_res = analysis_service(analysis_req)
        except Exception as e:
            logger.error(f"Trace {trace_id}: Agent 3 Analysis failed with exception: {e}")
            analysis_res = AnalysisResponse(
                trace_id=trace_id,
                safety_status="INSUFFICIENT_EVIDENCE",
                risk_level="MEDIUM",
                confidence="low",
                uncertainty_reasons=["Analysis engine failure occurred during safety check."],
            )

        ana_ms = round((time.perf_counter() - start_ana) * 1000)
        execution_steps.append(
            ExecutionStep(
                agent="analysis",
                action=f"safety_reasoning:{analysis_res.safety_status}",
                status=analysis_res.safety_status,
                duration_ms=ana_ms,
                summary=f"Safety Verdict: {analysis_res.safety_status}",
            )
        )

    # Step 4: Execute Agent 4 (Recommendation & Response)
    execution_path.append("response")
    start_resp = time.perf_counter()
    response_req = ResponseRequest(
        trace_id=trace_id,
        query=user_query,
        intent=triage_output.primary_intent.value,
        triage_status=triage_output.triage_status.value,
        evidence=retrieval_res.candidates,
        analysis=analysis_res,
        nutrient_constraints=triage_output.nutrient_constraints,
        constraints=triage_output.constraints,
        preferences=triage_output.preferences,
        nutrients=triage_output.nutrients,
    )
    response_res = response_service(response_req)
    resp_ms = round((time.perf_counter() - start_resp) * 1000)

    execution_steps.append(
        ExecutionStep(
            agent="response",
            action="grounded_response_generation",
            status="OK",
            duration_ms=resp_ms,
            summary="Generated grounded response",
        )
    )

    return ChatResponse(
        trace_id=trace_id,
        session_id=request.session_id,
        query=user_query,
        execution_path=execution_path,
        execution_steps=execution_steps,
        triage_output=triage_output.model_dump(),
        sources=response_res.sources,
        final_response=response_res.answer,
    )
