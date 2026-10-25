from typing import Literal

from pydantic import BaseModel, Field

ClaimStatus = Literal["waiting", "in_progress", "waiting_for_sign_off", "decided"]
DecisionValue = Literal["approve", "decline", "refer"]


class QueueClaim(BaseModel):
    claim_id: str
    claim_type: str
    summary: str
    submitted_on: str
    amount_claimed: float
    status: ClaimStatus
    decision: DecisionValue | None
    payout: float | None


class QueueResponse(BaseModel):
    claims: list[QueueClaim]
    total: int


class ActivityCreate(BaseModel):
    step: str = Field(min_length=1)
    message: str = Field(min_length=1)


class Activity(ActivityCreate):
    activity_id: int
    claim_id: str
    created_at: str


class DecisionCreate(BaseModel):
    decision: DecisionValue
    payout: float = Field(ge=0)
    rationale: str = Field(min_length=1)
    policy_section: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)


class Decision(DecisionCreate):
    claim_id: str


class SignOffCreate(BaseModel):
    handler_id: str = Field(min_length=1)


class SignOff(SignOffCreate):
    claim_id: str
    signed_at: str


class PaymentCreate(BaseModel):
    amount: float = Field(ge=0)


class Payment(PaymentCreate):
    claim_id: str
    recorded_at: str


class ClaimDetail(BaseModel):
    claim: dict[str, object]
    policy: dict[str, object]
    customer: dict[str, object]
    plan: dict[str, object]
    status: ClaimStatus
    decision: Decision | None
    activities: list[Activity]
    sign_off: SignOff | None
    payment: Payment | None


class DecisionContext(BaseModel):
    claim: dict[str, object]
    policy: dict[str, object]
    previous_claims: list[dict[str, object]]


class InstructionsResponse(BaseModel):
    instructions: str


class RunRequest(BaseModel):
    thread_id: str = Field(min_length=1)


class RunResponse(RunRequest):
    claim_id: str
    status: Literal["started"]
