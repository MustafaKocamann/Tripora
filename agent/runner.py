import json
import os
from typing import Literal, cast
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr


class ClaimDecision(BaseModel):
    decision: Literal["approve", "decline", "refer"]
    payout: float = Field(ge=0)
    rationale: str = Field(min_length=1)
    policy_section: str = Field(min_length=1)


def _api_base_url() -> str:
    return os.getenv("UNDERCOVER_API_URL", "http://127.0.0.1:8000")


def _request_json(method: str, path: str, payload: dict[str, object] | None) -> object:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        f"{_api_base_url()}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as error:
        detail = json.loads(error.read().decode()).get("detail", str(error))
        raise RuntimeError(str(detail)) from error


@tool
def get_claim_context(claim_id: str) -> str:
    """Get the privacy-safe claim context and policy wording."""
    return json.dumps(
        _request_json("GET", f"/api/agent/claims/{claim_id}/context", None)
    )


@tool
def add_claim_activity(claim_id: str, step: str, message: str) -> str:
    """Record one short, non-personal agent activity."""
    return json.dumps(
        _request_json(
            "POST",
            f"/api/claims/{claim_id}/activities",
            {"step": step, "message": message},
        )
    )


@tool
def record_claim_decision(
    claim_id: str,
    thread_id: str,
    decision: Literal["approve", "decline", "refer"],
    payout: float,
    rationale: str,
    policy_section: str,
) -> str:
    """Record the final structured decision on a claim."""
    return json.dumps(
        _request_json(
            "POST",
            f"/api/claims/{claim_id}/decisions",
            {
                "decision": decision,
                "payout": payout,
                "rationale": rationale,
                "policy_section": policy_section,
                "thread_id": thread_id,
            },
        )
    )


@tool
def pay_claim(claim_id: str, amount: float) -> str:
    """Attempt a guarded simulated claim payment."""
    return json.dumps(
        _request_json("POST", f"/api/claims/{claim_id}/payments", {"amount": amount})
    )


def _stub_decision(claim_id: str, context: dict[str, object]) -> ClaimDecision:
    scenarios = {
        "CLM-1002": ClaimDecision(
            decision="decline",
            payout=0,
            rationale="The evidence does not satisfy the covered baggage-loss terms. Section 6 requires proof of a covered loss.",
            policy_section="Section 6",
        ),
        "CLM-1003": ClaimDecision(
            decision="refer",
            payout=0,
            rationale="The medical evidence requires a handler's judgment before coverage can be confirmed. Section 8 sets the medical coverage conditions.",
            policy_section="Section 8",
        ),
        "CLM-1008": ClaimDecision(
            decision="approve",
            payout=1250,
            rationale="The cancellation evidence meets the covered-event terms. Section 3 supports a $1,250.00 payout subject to handler sign-off.",
            policy_section="Section 3",
        ),
    }
    if claim_id in scenarios:
        return scenarios[claim_id]
    claim = cast(dict[str, object], context["claim"])
    payout = min(float(cast(float, claim["amount_claimed"])), 1000.0)
    return ClaimDecision(
        decision="approve",
        payout=payout,
        rationale="The submitted evidence meets the covered-event terms. Section 2 supports the calculated payout.",
        policy_section="Section 2",
    )


def _decision_prompt(claim_id: str, context: dict[str, object]) -> str:
    return (
        f"Decide claim {claim_id}. This context came from the privacy-safe API: "
        f"{json.dumps(context)}"
    )


def _invoke_decision(
    claim_id: str,
    thread_id: str,
    context: dict[str, object],
    instructions: str,
) -> ClaimDecision:
    model_name = os.getenv("MODEL_NAME", "openai/gpt-6-luna")
    api_key = os.environ["OPENROUTER_API_KEY"]
    model = ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        base_url="https://openrouter.ai/api/v1",
        reasoning_effort="low",
    )
    workflow = create_agent(
        model=model,
        tools=[
            get_claim_context,
            add_claim_activity,
            record_claim_decision,
            pay_claim,
        ],
        system_prompt=instructions,
        response_format=ClaimDecision,
    )
    result = workflow.invoke(
        {
            "messages": [
                {"role": "user", "content": _decision_prompt(claim_id, context)}
            ]
        },
        config={"configurable": {"thread_id": thread_id}},
    )
    return ClaimDecision.model_validate(result["structured_response"])


def _record_activity(claim_id: str, step: str, message: str) -> None:
    _request_json(
        "POST",
        f"/api/claims/{claim_id}/activities",
        {"step": step, "message": message},
    )


def run(claim_id: str, thread_id: str) -> dict[str, object]:
    """Run the claim agent entry point."""
    try:
        _record_activity(claim_id, "reading", "Reading claim evidence")
        context = cast(
            dict[str, object],
            _request_json("GET", f"/api/agent/claims/{claim_id}/context", None),
        )
        instructions_response = cast(
            dict[str, object], _request_json("GET", "/api/agent/instructions", None)
        )
        _record_activity(claim_id, "policy", "Applying the policy wording")
        if os.getenv("UNDERCOVER_STUB_AGENT") == "1":
            decision = _stub_decision(claim_id, context)
        else:
            decision = _invoke_decision(
                claim_id,
                thread_id,
                context,
                str(instructions_response["instructions"]),
            )
        payload: dict[str, object] = {
            **decision.model_dump(),
            "thread_id": thread_id,
        }
        _request_json("POST", f"/api/claims/{claim_id}/decisions", payload)
        if decision.decision == "approve":
            try:
                _request_json(
                    "POST",
                    f"/api/claims/{claim_id}/payments",
                    {"amount": decision.payout},
                )
            except RuntimeError as error:
                if str(error) != "Handler sign-off required":
                    raise
                _record_activity(
                    claim_id,
                    "safeguard",
                    "Payment is waiting for handler sign-off",
                )
        return decision.model_dump()
    except Exception:
        _record_activity(claim_id, "failed", "Agent run failed")
        raise
