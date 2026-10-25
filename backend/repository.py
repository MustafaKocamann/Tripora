import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import cast

from backend.database import JsonObject, connect
from backend.schemas import ActivityCreate, DecisionCreate, PaymentCreate, SignOffCreate


def _decode(value: str) -> JsonObject:
    return cast(JsonObject, json.loads(value))


def _required_row(
    connection: sqlite3.Connection, query: str, parameters: tuple[object, ...]
) -> sqlite3.Row:
    row = connection.execute(query, parameters).fetchone()
    if row is None:
        raise ValueError("Claim not found")
    return row


def _company(connection: sqlite3.Connection) -> JsonObject:
    row = connection.execute(
        "SELECT data FROM settings WHERE key = 'company'"
    ).fetchone()
    if row is None:
        raise ValueError("Company settings not found")
    return _decode(str(row["data"]))


def list_claims(path: Path | None = None) -> list[JsonObject]:
    """List queue claims with their current decisions."""
    with closing(connect(path)) as connection:
        rows = connection.execute(
            """
            SELECT claims.data, claims.status, decisions.decision, decisions.payout
            FROM claims
            LEFT JOIN decisions USING (claim_id)
            ORDER BY claims.claim_id
            """
        ).fetchall()
    claims: list[JsonObject] = []
    for row in rows:
        source = _decode(str(row["data"]))
        claims.append(
            {
                "claim_id": source["claim_id"],
                "claim_type": source["claim_type"],
                "summary": source["summary"],
                "submitted_on": source["submitted_on"],
                "amount_claimed": source["amount_claimed"],
                "status": row["status"],
                "decision": row["decision"],
                "payout": row["payout"],
            }
        )
    return claims


def _private_values(customer: JsonObject, policy: JsonObject) -> list[str]:
    values = [
        customer.get("name"),
        customer.get("email"),
        customer.get("phone"),
        customer.get("date_of_birth"),
    ]
    address = cast(JsonObject, customer.get("address", {}))
    values.extend(address.values())
    values.extend(cast(list[object], policy.get("travelers", [])))
    return sorted(
        {str(value) for value in values if value and len(str(value)) >= 4},
        key=len,
        reverse=True,
    )


def _redact_text(value: object, private_values: list[str]) -> str:
    text = str(value)
    for private_value in private_values:
        text = re.sub(re.escape(private_value), "[REDACTED]", text, flags=re.IGNORECASE)
    return text


def _sanitize_claim(claim: JsonObject, private_values: list[str]) -> JsonObject:
    items = cast(list[JsonObject], claim["items"])
    documents = cast(list[JsonObject], claim["documents"])
    return {
        "claim_id": claim["claim_id"],
        "claim_type": claim["claim_type"],
        "submitted_on": claim["submitted_on"],
        "incident_date": claim["incident_date"],
        "incident_location": _redact_text(claim["incident_location"], private_values),
        "summary": _redact_text(claim["summary"], private_values),
        "story": _redact_text(claim["story"], private_values),
        "items": [
            {
                "description": _redact_text(item["description"], private_values),
                "category": item["category"],
                "amount": item["amount"],
            }
            for item in items
        ],
        "amount_claimed": claim["amount_claimed"],
        "documents": [
            {
                "label": _redact_text(document["name"], private_values),
                "type": document["type"],
                "content": _redact_text(document["content"], private_values),
            }
            for document in documents
        ],
    }


def _sanitize_coverage(plan: JsonObject) -> JsonObject:
    return {key: value for key, value in plan.items() if key not in {"name", "plan_id"}}


def get_decision_context(claim_id: str, path: Path | None = None) -> JsonObject:
    """Return the allowlisted, privacy-safe agent context."""
    with closing(connect(path)) as connection:
        claim_row = _required_row(
            connection, "SELECT data FROM claims WHERE claim_id = ?", (claim_id,)
        )
        claim = _decode(str(claim_row["data"]))
        policy_row = connection.execute(
            "SELECT data FROM policies WHERE policy_id = ?", (claim["policy_id"],)
        ).fetchone()
        customer_row = connection.execute(
            "SELECT data FROM customers WHERE customer_id = ?",
            (claim["customer_id"],),
        ).fetchone()
        if policy_row is None or customer_row is None:
            raise ValueError("Related claim data not found")
        policy = _decode(str(policy_row["data"]))
        customer = _decode(str(customer_row["data"]))
        plan_row = connection.execute(
            "SELECT data FROM plans WHERE plan_id = ?", (policy["plan"],)
        ).fetchone()
        if plan_row is None:
            raise ValueError("Plan not found")
        wording_row = connection.execute(
            "SELECT data FROM settings WHERE key = 'policy_wording'"
        ).fetchone()
        if wording_row is None:
            raise ValueError("Policy wording not found")
    private_values = _private_values(customer, policy)
    previous_claims = cast(list[JsonObject], customer.get("previous_claims", []))
    return {
        "claim": _sanitize_claim(claim, private_values),
        "policy": {
            "plan": policy["plan"],
            "add_ons": policy["add_ons"],
            "purchased_on": policy["purchased_on"],
            "trip": policy["trip"],
            "status": policy["status"],
            "coverage": _sanitize_coverage(_decode(str(plan_row["data"]))),
            "wording": str(wording_row["data"]),
        },
        "previous_claims": [
            {
                "claim_id": previous["claim_id"],
                "filed_on": previous["filed_on"],
                "incident_date": previous["incident_date"],
                "claim_type": previous["claim_type"],
                "summary": _redact_text(previous["summary"], private_values),
                "outcome": previous["outcome"],
                "amount_paid": previous["amount_paid"],
            }
            for previous in previous_claims
        ],
    }


def get_claim_detail(claim_id: str, path: Path | None = None) -> JsonObject:
    """Return a full handler-facing claim record."""
    with closing(connect(path)) as connection:
        claim_row = _required_row(
            connection,
            "SELECT data, status FROM claims WHERE claim_id = ?",
            (claim_id,),
        )
        claim = _decode(str(claim_row["data"]))
        policy_row = connection.execute(
            "SELECT data FROM policies WHERE policy_id = ?", (claim["policy_id"],)
        ).fetchone()
        customer_row = connection.execute(
            "SELECT data FROM customers WHERE customer_id = ?",
            (claim["customer_id"],),
        ).fetchone()
        if policy_row is None or customer_row is None:
            raise ValueError("Related claim data not found")
        policy = _decode(str(policy_row["data"]))
        customer = _decode(str(customer_row["data"]))
        plan_row = connection.execute(
            "SELECT data FROM plans WHERE plan_id = ?", (policy["plan"],)
        ).fetchone()
        if plan_row is None:
            raise ValueError("Plan not found")
        decision_row = connection.execute(
            "SELECT * FROM decisions WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        activity_rows = connection.execute(
            "SELECT * FROM activities WHERE claim_id = ? ORDER BY activity_id",
            (claim_id,),
        ).fetchall()
        sign_off_row = connection.execute(
            "SELECT * FROM sign_offs WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        payment_row = connection.execute(
            "SELECT * FROM payments WHERE claim_id = ?", (claim_id,)
        ).fetchone()
    return {
        "claim": claim,
        "policy": policy,
        "customer": customer,
        "plan": _decode(str(plan_row["data"])),
        "status": claim_row["status"],
        "decision": dict(decision_row) if decision_row else None,
        "activities": [dict(row) for row in activity_rows],
        "sign_off": dict(sign_off_row) if sign_off_row else None,
        "payment": dict(payment_row) if payment_row else None,
    }


def add_activity(
    claim_id: str, activity: ActivityCreate, path: Path | None = None
) -> JsonObject:
    """Append an ordered activity to a claim."""
    with closing(connect(path)) as connection:
        _required_row(
            connection, "SELECT claim_id FROM claims WHERE claim_id = ?", (claim_id,)
        )
        cursor = connection.execute(
            "INSERT INTO activities (claim_id, step, message) VALUES (?, ?, ?)",
            (claim_id, activity.step, activity.message),
        )
        row = connection.execute(
            "SELECT * FROM activities WHERE activity_id = ?", (cursor.lastrowid,)
        ).fetchone()
        connection.commit()
    assert row is not None
    return dict(row)


def mark_in_progress(claim_id: str, path: Path | None = None) -> None:
    """Move a waiting claim into progress."""
    with closing(connect(path)) as connection:
        row = _required_row(
            connection, "SELECT status FROM claims WHERE claim_id = ?", (claim_id,)
        )
        if row["status"] != "waiting":
            raise ValueError("Claim is not waiting")
        connection.execute(
            "UPDATE claims SET status = 'in_progress' WHERE claim_id = ?", (claim_id,)
        )
        connection.commit()


def record_decision(
    claim_id: str, decision: DecisionCreate, path: Path | None = None
) -> JsonObject:
    """Record a decision and apply its next queue state."""
    with closing(connect(path)) as connection:
        claim_row = _required_row(
            connection, "SELECT data FROM claims WHERE claim_id = ?", (claim_id,)
        )
        claim = _decode(str(claim_row["data"]))
        if decision.decision != "approve" and decision.payout != 0:
            raise ValueError("Declined and referred claims must have a zero payout")
        if decision.payout > float(cast(float, claim["amount_claimed"])):
            raise ValueError("Payout cannot exceed the claimed amount")
        limit = float(cast(float, _company(connection)["payout_approval_limit"]))
        status = (
            "waiting_for_sign_off"
            if decision.decision == "approve" and decision.payout > limit
            else "decided"
        )
        try:
            connection.execute(
                """
                INSERT INTO decisions (
                    claim_id, decision, payout, rationale, policy_section, thread_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    decision.decision,
                    decision.payout,
                    decision.rationale,
                    decision.policy_section,
                    decision.thread_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Claim already has a decision") from error
        connection.execute(
            "UPDATE claims SET status = ? WHERE claim_id = ?", (status, claim_id)
        )
        connection.execute(
            "INSERT INTO activities (claim_id, step, message) VALUES (?, ?, ?)",
            (claim_id, "decision", f"Decision recorded: {decision.decision}"),
        )
        row = connection.execute(
            "SELECT * FROM decisions WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        connection.commit()
    assert row is not None
    return dict(row)


def sign_off(
    claim_id: str, sign_off_request: SignOffCreate, path: Path | None = None
) -> JsonObject:
    """Record handler approval for a high-value payout."""
    with closing(connect(path)) as connection:
        decision = _required_row(
            connection,
            "SELECT decision, payout FROM decisions WHERE claim_id = ?",
            (claim_id,),
        )
        handler = connection.execute(
            "SELECT data FROM handlers WHERE handler_id = ?",
            (sign_off_request.handler_id,),
        ).fetchone()
        if handler is None:
            raise ValueError("Handler not found")
        handler_data = _decode(str(handler["data"]))
        limit = float(cast(float, _company(connection)["payout_approval_limit"]))
        if decision["decision"] != "approve" or float(decision["payout"]) <= limit:
            raise ValueError("Claim does not require sign-off")
        if not bool(handler_data["can_approve_over_limit"]):
            raise ValueError("Handler cannot approve over the limit")
        try:
            connection.execute(
                "INSERT INTO sign_offs (claim_id, handler_id) VALUES (?, ?)",
                (claim_id, sign_off_request.handler_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Claim already has sign-off") from error
        connection.execute(
            "UPDATE claims SET status = 'decided' WHERE claim_id = ?", (claim_id,)
        )
        connection.execute(
            "INSERT INTO activities (claim_id, step, message) VALUES (?, ?, ?)",
            (claim_id, "sign_off", "Handler sign-off recorded"),
        )
        row = connection.execute(
            "SELECT * FROM sign_offs WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        connection.commit()
    assert row is not None
    return dict(row)


def record_payment(
    claim_id: str, payment: PaymentCreate, path: Path | None = None
) -> JsonObject:
    """Record a simulated payment after all safeguards pass."""
    with closing(connect(path)) as connection:
        decision = _required_row(
            connection,
            "SELECT decision, payout FROM decisions WHERE claim_id = ?",
            (claim_id,),
        )
        if decision["decision"] != "approve":
            raise ValueError("Only approved claims can be paid")
        if round(float(decision["payout"]), 2) != round(payment.amount, 2):
            raise ValueError("Payment must match the approved payout")
        limit = float(cast(float, _company(connection)["payout_approval_limit"]))
        if payment.amount > limit:
            approved = connection.execute(
                "SELECT 1 FROM sign_offs WHERE claim_id = ?", (claim_id,)
            ).fetchone()
            if approved is None:
                raise ValueError("Handler sign-off required")
        try:
            connection.execute(
                "INSERT INTO payments (claim_id, amount) VALUES (?, ?)",
                (claim_id, payment.amount),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Claim already has a payment") from error
        connection.execute(
            "UPDATE claims SET status = 'decided' WHERE claim_id = ?", (claim_id,)
        )
        connection.execute(
            "INSERT INTO activities (claim_id, step, message) VALUES (?, ?, ?)",
            (claim_id, "payment", "Simulated payment recorded"),
        )
        row = connection.execute(
            "SELECT * FROM payments WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        connection.commit()
    assert row is not None
    return dict(row)
