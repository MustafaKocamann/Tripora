from fastapi.testclient import TestClient


def decision(decision_value: str, payout: float) -> dict[str, object]:
    return {
        "decision": decision_value,
        "payout": payout,
        "rationale": "The claim follows the covered event rule. Section 2 sets the payable amount.",
        "policy_section": "Section 2",
        "thread_id": "thread-api",
    }


def test_queue_and_full_claim(client: TestClient) -> None:
    queue = client.get("/api/claims")
    assert queue.status_code == 200
    assert queue.json()["total"] == 25
    assert all(item["status"] == "waiting" for item in queue.json()["claims"])
    assert all(item["claim_id"] != "CLM-1901" for item in queue.json()["claims"])

    response = client.get("/api/claims/CLM-1001")
    assert response.status_code == 200
    body = response.json()
    assert body["claim"]["documents"]
    assert body["policy"]["plan"] == "premium"
    assert body["customer"]["previous_claims"]
    assert body["plan"]["trip_delay_max"] == 800.0
    assert body["activities"] == []


def test_missing_claim_and_activity_order(client: TestClient) -> None:
    assert client.get("/api/claims/missing").status_code == 404
    first = client.post(
        "/api/claims/CLM-1001/activities",
        json={"step": "read", "message": "Read the claim"},
    )
    second = client.post(
        "/api/claims/CLM-1001/activities",
        json={"step": "policy", "message": "Checked Section 2"},
    )
    assert first.status_code == 200
    assert second.json()["activity_id"] > first.json()["activity_id"]
    detail = client.get("/api/claims/CLM-1001").json()
    assert [item["step"] for item in detail["activities"]] == ["read", "policy"]


def test_openapi_operations_are_explicit_and_inputs_required(
    client: TestClient,
) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    operation_ids: list[str] = []
    for operations in paths.values():
        for operation in operations.values():
            operation_ids.append(operation["operationId"])
            assert operation["summary"]
            for parameter in operation.get("parameters", []):
                assert parameter["required"] is True
            if "requestBody" in operation:
                assert operation["requestBody"]["required"] is True
    assert len(operation_ids) == len(set(operation_ids))
