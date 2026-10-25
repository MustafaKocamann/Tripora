import type { ClaimDetail } from "../types";
import { formatMoney } from "../format";

interface ClaimDetailPanelProps {
  detail: ClaimDetail | null;
  busy: boolean;
  onRun: () => void;
  onSignOff: () => void;
  onPay: () => void;
}

export function ClaimDetailPanel({
  detail,
  busy,
  onRun,
  onSignOff,
  onPay,
}: Readonly<ClaimDetailPanelProps>) {
  if (!detail)
    return (
      <section className="detail-panel center-state">Select a claim.</section>
    );

  const { claim, customer, policy, decision } = detail;
  const canSignOff =
    detail.status === "waiting_for_sign_off" && detail.sign_off === null;
  const canPay =
    decision?.decision === "approve" &&
    detail.payment === null &&
    (decision.payout <= 1000 || detail.sign_off !== null);

  return (
    <section className="detail-panel" aria-labelledby="claim-heading">
      <div className="detail-hero">
        <div>
          <p className="eyebrow">
            {claim.claim_type.replaceAll("_", " ")} · {claim.incident_date}
          </p>
          <h2 id="claim-heading">{claim.summary}</h2>
          <p>{claim.story}</p>
        </div>
        <div className="amount-block">
          <span>Claimed</span>
          <strong>{formatMoney(claim.amount_claimed)}</strong>
        </div>
      </div>

      <div className="actions">
        {detail.status === "waiting" && (
          <button className="primary" disabled={busy} onClick={onRun}>
            Run agent
          </button>
        )}
        {canSignOff && (
          <button className="approval" disabled={busy} onClick={onSignOff}>
            Sign off payout
          </button>
        )}
        {canPay && (
          <button className="secondary" disabled={busy} onClick={onPay}>
            Record payment
          </button>
        )}
      </div>

      {decision && (
        <article className={`decision-card decision-${decision.decision}`}>
          <div>
            <p className="eyebrow">Agent decision</p>
            <h3>{decision.decision}</h3>
          </div>
          <strong>{formatMoney(decision.payout)}</strong>
          <p>{decision.rationale}</p>
          <code>{decision.policy_section}</code>
        </article>
      )}

      <div className="detail-grid">
        <article className="card">
          <h3>Customer</h3>
          <dl>
            <dt>Name</dt>
            <dd>{customer.name}</dd>
            <dt>Email</dt>
            <dd>{customer.email}</dd>
            <dt>Phone</dt>
            <dd>{customer.phone}</dd>
            <dt>Date of birth</dt>
            <dd>{customer.date_of_birth}</dd>
            <dt>Address</dt>
            <dd>
              {customer.address.street}, {customer.address.city},{" "}
              {customer.address.state} {customer.address.zip}
            </dd>
          </dl>
        </article>

        <article className="card">
          <h3>Policy</h3>
          <dl>
            <dt>Plan</dt>
            <dd>{policy.plan}</dd>
            <dt>Status</dt>
            <dd>{policy.status}</dd>
            <dt>Destination</dt>
            <dd>{policy.trip.destination}</dd>
            <dt>Trip dates</dt>
            <dd>
              {policy.trip.departs_on} – {policy.trip.returns_on}
            </dd>
            <dt>Trip cost</dt>
            <dd>{formatMoney(policy.trip.trip_cost)}</dd>
          </dl>
        </article>
      </div>

      <article className="card">
        <h3>Claimed items</h3>
        <ul className="item-list">
          {claim.items.map((item) => (
            <li key={`${item.category}-${item.description}`}>
              <span>{item.description}</span>
              <strong>{formatMoney(item.amount)}</strong>
            </li>
          ))}
        </ul>
      </article>

      <article className="card">
        <h3>Supporting documents</h3>
        <div className="documents">
          {claim.documents.map((document) => (
            <details key={`${document.type}-${document.name}`}>
              <summary>{document.name}</summary>
              <p>{document.content}</p>
            </details>
          ))}
        </div>
      </article>

      <article className="card">
        <h3>Previous claims</h3>
        {customer.previous_claims.length === 0 ? (
          <p>No previous claims.</p>
        ) : (
          <ul className="history-list">
            {customer.previous_claims.map((previous) => (
              <li key={previous.claim_id}>
                <code>{previous.claim_id}</code>
                <span>{previous.summary}</span>
                <strong>{formatMoney(previous.amount_paid)}</strong>
              </li>
            ))}
          </ul>
        )}
      </article>

      <article className="card activity-card">
        <h3>Agent activity</h3>
        {detail.activities.length === 0 ? (
          <p>No agent activity yet.</p>
        ) : (
          <ol>
            {detail.activities.map((activity) => (
              <li key={activity.activity_id}>
                <span>{activity.step.replaceAll("_", " ")}</span>
                <p>{activity.message}</p>
              </li>
            ))}
          </ol>
        )}
      </article>
    </section>
  );
}
