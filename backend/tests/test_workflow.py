from fastapi.testclient import TestClient

from backend.tests.test_claims_api import decision


def test_low_value_approval_and_payment(client: TestClient) -> None:
    recorded = client.post(
        "/api/claims/CLM-1001/decisions", json=decision("approve", 420.0)
    )
    assert recorded.status_code == 200
    assert client.get("/api/claims/CLM-1001").json()["status"] == "decided"
    payment = client.post("/api/claims/CLM-1001/payments", json={"amount": 420.0})
    assert payment.status_code == 200
    assert payment.json()["amount"] == 420.0


def test_high_value_payment_requires_sign_off(client: TestClient) -> None:
    recorded = client.post(
        "/api/claims/CLM-1002/decisions", json=decision("approve", 1150.0)
    )
    assert recorded.status_code == 200
    assert client.get("/api/claims/CLM-1002").json()["status"] == "waiting_for_sign_off"
    blocked = client.post("/api/claims/CLM-1002/payments", json={"amount": 1150.0})
    assert blocked.status_code == 409
    assert blocked.json() == {"detail": "Handler sign-off required"}
    assert client.get("/api/claims/CLM-1002").json()["payment"] is None

    sign_off = client.post(
        "/api/claims/CLM-1002/sign-offs", json={"handler_id": "HND-01"}
    )
    assert sign_off.status_code == 200
    wrong = client.post("/api/claims/CLM-1002/payments", json={"amount": 1000.0})
    assert wrong.status_code == 409
    payment = client.post("/api/claims/CLM-1002/payments", json={"amount": 1150.0})
    assert payment.status_code == 200


def test_decline_and_refer_cannot_be_paid(client: TestClient) -> None:
    for claim_id, value in [("CLM-1003", "decline"), ("CLM-1004", "refer")]:
        assert (
            client.post(
                f"/api/claims/{claim_id}/decisions", json=decision(value, 0)
            ).status_code
            == 200
        )
        blocked = client.post(f"/api/claims/{claim_id}/payments", json={"amount": 0})
        assert blocked.status_code == 409
        assert blocked.json() == {"detail": "Only approved claims can be paid"}


def test_invalid_decisions_and_duplicate_writes_are_rejected(
    client: TestClient,
) -> None:
    nonzero_decline = client.post(
        "/api/claims/CLM-1005/decisions", json=decision("decline", 1)
    )
    assert nonzero_decline.status_code == 409
    too_high = client.post(
        "/api/claims/CLM-1005/decisions", json=decision("approve", 500)
    )
    assert too_high.status_code == 409

    assert (
        client.post(
            "/api/claims/CLM-1005/decisions", json=decision("approve", 200)
        ).status_code
        == 200
    )
    duplicate = client.post(
        "/api/claims/CLM-1005/decisions", json=decision("approve", 200)
    )
    assert duplicate.status_code == 409
