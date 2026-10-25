from fastapi import APIRouter, HTTPException

from backend import repository
from backend.schemas import (
    Activity,
    ActivityCreate,
    ClaimDetail,
    Decision,
    DecisionCreate,
    Payment,
    PaymentCreate,
    QueueResponse,
    SignOff,
    SignOffCreate,
)

router = APIRouter(prefix="/api")


def _http_error(error: ValueError) -> HTTPException:
    message = str(error)
    status = 404 if message.endswith("not found") else 409
    return HTTPException(status_code=status, detail=message)


@router.get("/claims", operation_id="list_claims", response_model=QueueResponse)
def list_claims() -> QueueResponse:
    """Return the claims queue."""
    claims = repository.list_claims()
    return QueueResponse.model_validate({"claims": claims, "total": len(claims)})


@router.get("/claims/{claim_id}", operation_id="get_claim", response_model=ClaimDetail)
def get_claim(claim_id: str) -> ClaimDetail:
    """Return one complete handler-facing claim."""
    try:
        return ClaimDetail.model_validate(repository.get_claim_detail(claim_id))
    except ValueError as error:
        raise _http_error(error) from error


@router.post(
    "/claims/{claim_id}/activities",
    operation_id="add_claim_activity",
    response_model=Activity,
)
def add_claim_activity(claim_id: str, activity: ActivityCreate) -> Activity:
    """Append one activity to a claim."""
    try:
        return Activity.model_validate(repository.add_activity(claim_id, activity))
    except ValueError as error:
        raise _http_error(error) from error


@router.post(
    "/claims/{claim_id}/decisions",
    operation_id="record_claim_decision",
    response_model=Decision,
)
def record_claim_decision(claim_id: str, decision: DecisionCreate) -> Decision:
    """Record the agent decision on a claim."""
    try:
        return Decision.model_validate(repository.record_decision(claim_id, decision))
    except ValueError as error:
        raise _http_error(error) from error


@router.post(
    "/claims/{claim_id}/sign-offs",
    operation_id="sign_off_claim",
    response_model=SignOff,
)
def sign_off_claim(claim_id: str, request: SignOffCreate) -> SignOff:
    """Sign off a high-value approved claim."""
    try:
        return SignOff.model_validate(repository.sign_off(claim_id, request))
    except ValueError as error:
        raise _http_error(error) from error


@router.post(
    "/claims/{claim_id}/payments",
    operation_id="record_claim_payment",
    response_model=Payment,
)
def record_claim_payment(claim_id: str, payment: PaymentCreate) -> Payment:
    """Record a guarded simulated payment."""
    try:
        return Payment.model_validate(repository.record_payment(claim_id, payment))
    except ValueError as error:
        raise _http_error(error) from error
