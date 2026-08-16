"""Orchestrator Engine for EviBite AI (Owned by Member 1).

Manages conditional multi-agent routing, message envelope propagation,
trace ID tracking, and execution logging across Triage, Retrieval, Analysis,
and Response agents.
"""

from backend.app.agents.agent_stubs import (
    AnalysisRequest,
    RetrievalRequest,
    ResponseRequest,
    stub_analysis_service,
    stub_response_service,
)
from backend.app.agents.retrieval.service import retrieval_service
from backend.app.agents.triage.service import triage_message
from backend.app.models.messages import ChatRequest, ChatResponse, ExecutionStep
from backend.app.models.triage import RouteAgent, TriageRequest, TriageStatus
from backend.app.agents.recommendation_response.service import response_service

def run_orchestration(request: ChatRequest) -> ChatResponse:
    user_query = request.message.strip()
    execution_steps: list[ExecutionStep] = []
    execution_path: list[str] = []

    # Step 1: Execute Agent 1 (Triage & Routing)
    triage_req = TriageRequest(message=user_query, session_id=request.session_id)
    triage_output = triage_message(triage_req)
    trace_id = triage_output.trace_id

    execution_path.append("triage")
    execution_steps.append(
        ExecutionStep(
            agent="triage",
            action=f"intent_extraction:{triage_output.primary_intent}",
            status=triage_output.triage_status.value,
        )
    )

    # Early exit if clarification is required
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

    # Early exit if query is unsupported
    if triage_output.triage_status == TriageStatus.UNSUPPORTED:
        execution_path.append("response")
        resp_stub = stub_response_service(
            ResponseRequest(
                trace_id=trace_id,
                query=user_query,
                intent=triage_output.primary_intent.value,
                triage_status=triage_output.triage_status.value,
            )
        )
        execution_steps.append(
            ExecutionStep(
                agent="response",
                action="unsupported_query_handling",
                status="OK",
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

    # Step 2: Execute Agent 2 (Product Information Retrieval)
    execution_path.append("retrieval")
    retrieval_req = RetrievalRequest(
        trace_id=trace_id,
        query=user_query,
        intent=triage_output.primary_intent.value,
        products=[p.model_dump() for p in triage_output.products],
        category=triage_output.category,
        requested_fields=triage_output.requested_fields,
    )
    retrieval_res = retrieval_service(retrieval_req)
    execution_steps.append(
        ExecutionStep(
            agent="retrieval",
            action=f"candidate_retrieval:{len(retrieval_res.candidates)} candidates",
            status=retrieval_res.status,
        )
    )

    # Step 3: Execute Agent 3 (Nutrition & Allergen Analysis) if required
    analysis_res = None
    if (
        triage_output.routing.analysis_required
        or RouteAgent.ANALYSIS in triage_output.routing.required_agents
    ):
        execution_path.append("analysis")
        analysis_req = AnalysisRequest(
            trace_id=trace_id,
            primary_intent=triage_output.primary_intent.value,
            allergens=triage_output.allergens,
            nutrients=triage_output.nutrients,
            dietary_requirements=triage_output.dietary_requirements,
            evidence=retrieval_res.candidates,
        )
        analysis_res = stub_analysis_service(analysis_req)
        execution_steps.append(
            ExecutionStep(
                agent="analysis",
                action=f"safety_reasoning:{analysis_res.safety_status}",
                status=analysis_res.safety_status,
            )
        )

    # Step 4: Execute Agent 4 (Recommendation & Response)
    execution_path.append("response")
    response_req = ResponseRequest(
        trace_id=trace_id,
        query=user_query,
        intent=triage_output.primary_intent.value,
        triage_status=triage_output.triage_status.value,
        evidence=retrieval_res.candidates,
        analysis=analysis_res,
        constraints=triage_output.constraints,
        preferences=triage_output.preferences,
        nutrients=triage_output.nutrients,
    )
    response_res = response_service(response_req)
    execution_steps.append(
        ExecutionStep(
            agent="response",
            action="grounded_response_generation",
            status="OK",
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
