from typing import Literal

import pytest

from agent import runner
from agent.runner import ClaimDecision


class FakeApi:
    def __init__(self, payment_error: str | None = None) -> None:
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []
        self.payment_error = payment_error

    def __call__(
        self, method: str, path: str, payload: dict[str, object] | None
    ) -> object:
        self.calls.append((method, path, payload))
        if path.endswith("/context"):
            return {
                "claim": {"claim_id": "CLM-1001", "amount_claimed": 420.0},
                "policy": {"plan": "premium", "wording": "Section 2"},
                "previous_claims": [],
            }
        if path == "/api/agent/instructions":
            return {"instructions": "Decide from the supplied evidence."}
        if path.endswith("/payments") and self.payment_error:
            raise RuntimeError(self.payment_error)
        return payload or {}


def decision(
    value: Literal["approve", "decline", "refer"], payout: float
) -> ClaimDecision:
    return ClaimDecision(
        decision=value,
        payout=payout,
        rationale="The evidence meets the policy terms. Section 2 sets the result.",
        policy_section="Section 2",
    )


@pytest.mark.parametrize(
    ("value", "payout", "expects_payment"),
    [("approve", 420.0, True), ("decline", 0.0, False), ("refer", 0.0, False)],
)
def test_run_persists_stubbed_decisions(
    monkeypatch: pytest.MonkeyPatch,
    value: Literal["approve", "decline", "refer"],
    payout: float,
    expects_payment: bool,
) -> None:
    api = FakeApi()
    captured: list[tuple[str, str, dict[str, object], str]] = []

    def invoke(
        claim_id: str,
        thread_id: str,
        context: dict[str, object],
        instructions: str,
    ) -> ClaimDecision:
        captured.append((claim_id, thread_id, context, instructions))
        return decision(value, payout)

    monkeypatch.setattr(runner, "_request_json", api)
    monkeypatch.setattr(runner, "_invoke_decision", invoke)
    monkeypatch.delenv("UNDERCOVER_STUB_AGENT", raising=False)

    result = runner.run("CLM-1001", "thread-1")

    assert result["decision"] == value
    assert captured[0][2]["claim"]
    decision_calls = [call for call in api.calls if call[1].endswith("/decisions")]
    payment_calls = [call for call in api.calls if call[1].endswith("/payments")]
    assert len(decision_calls) == 1
    assert bool(payment_calls) is expects_payment


def test_high_value_approval_records_safeguard(monkeypatch: pytest.MonkeyPatch) -> None:
    api = FakeApi("Handler sign-off required")
    monkeypatch.setattr(runner, "_request_json", api)
    monkeypatch.setattr(
        runner,
        "_invoke_decision",
        lambda *_: decision("approve", 1250.0),
    )
    monkeypatch.delenv("UNDERCOVER_STUB_AGENT", raising=False)

    runner.run("CLM-1008", "thread-high")

    activities = [call[2] for call in api.calls if call[1].endswith("/activities")]
    assert {activity["step"] for activity in activities if activity} >= {
        "reading",
        "policy",
        "safeguard",
    }


def test_invalid_model_result_records_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    api = FakeApi()
    monkeypatch.setattr(runner, "_request_json", api)

    def fail(*_: object) -> ClaimDecision:
        raise ValueError("invalid decision")

    monkeypatch.setattr(runner, "_invoke_decision", fail)
    monkeypatch.delenv("UNDERCOVER_STUB_AGENT", raising=False)

    with pytest.raises(ValueError, match="invalid decision"):
        runner.run("CLM-1001", "thread-fail")

    assert not any(call[1].endswith("/decisions") for call in api.calls)
    assert any(
        call[2] and call[2].get("step") == "failed"
        for call in api.calls
        if call[1].endswith("/activities")
    )


def test_e2e_stub_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    api = FakeApi()
    monkeypatch.setattr(runner, "_request_json", api)
    monkeypatch.setenv("UNDERCOVER_STUB_AGENT", "1")
    result = runner.run("CLM-1002", "thread-stub")
    assert result["decision"] == "decline"


def test_tools_use_only_dedicated_api_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    api = FakeApi()
    monkeypatch.setattr(runner, "_request_json", api)
    runner.get_claim_context.invoke({"claim_id": "CLM-1001"})
    paths = {call[1] for call in api.calls}
    assert paths == {"/api/agent/claims/CLM-1001/context"}
    assert all("evals" not in path and "security" not in path for path in paths)
