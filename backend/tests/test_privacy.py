import json

import pytest
from fastapi.testclient import TestClient

from agent.runner import _decision_prompt


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


def test_agent_context_is_allowlisted_and_redacted(client: TestClient) -> None:
    full = client.get("/api/claims/CLM-1001").json()
    response = client.get("/api/agent/claims/CLM-1001/context")
    assert response.status_code == 200
    context = response.json()
    serialized = json.dumps(context).lower()

    assert context["claim"]["story"]
    assert context["claim"]["documents"]
    assert context["policy"]["coverage"]["trip_delay_max"] == 800.0
    assert context["policy"]["wording"]
    assert context["previous_claims"]

    forbidden_keys = {
        "name",
        "customer_id",
        "email",
        "phone",
        "address",
        "date_of_birth",
        "travelers",
    }
    assert _keys(context).isdisjoint(forbidden_keys)
    customer = full["customer"]
    private_values = [
        customer["name"],
        customer["email"],
        customer["phone"],
        customer["date_of_birth"],
        *customer["address"].values(),
        *full["policy"]["travelers"],
        customer["customer_id"],
    ]
    assert all(
        str(value).lower() not in serialized
        for value in private_values
        if len(str(value)) >= 4
    )
    assert "[redacted]" in serialized
    prompt = _decision_prompt("CLM-1001", context)
    assert all(
        str(value).lower() not in prompt.lower()
        for value in private_values
        if len(str(value)) >= 4
    )


def test_agent_instructions_are_read_only(client: TestClient) -> None:
    response = client.get("/api/agent/instructions")
    assert response.status_code == 200
    assert "UnderCover Agent" in response.json()["instructions"]
    assert client.post("/api/agent/instructions", json={}).status_code == 405


def test_run_endpoint_marks_claim_and_uses_background_task(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "backend.api._run_agent",
        lambda claim_id, thread_id: calls.append((claim_id, thread_id)),
    )
    response = client.post(
        "/api/claims/CLM-1001/runs", json={"thread_id": "thread-privacy"}
    )
    assert response.status_code == 202
    assert calls == [("CLM-1001", "thread-privacy")]
    detail = client.get("/api/claims/CLM-1001").json()
    assert detail["status"] == "in_progress"
    assert detail["activities"][0]["step"] == "started"
