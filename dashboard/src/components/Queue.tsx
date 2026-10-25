import type { ClaimStatus, QueueClaim } from "../types";
import { formatMoney } from "../format";

const labels: Record<ClaimStatus, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  waiting_for_sign_off: "Waiting for sign-off",
  decided: "Decided",
};

interface QueueProps {
  claims: QueueClaim[];
  selectedId: string | null;
  onSelect: (claimId: string) => void;
}

export function Queue({ claims, selectedId, onSelect }: Readonly<QueueProps>) {
  return (
    <section className="queue-panel" aria-labelledby="queue-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Work queue</p>
          <h2 id="queue-heading">Claims</h2>
        </div>
        <span className="count">{claims.length}</span>
      </div>
      {claims.length === 0 ? (
        <p className="empty-state">No claims in the queue.</p>
      ) : (
        <ul className="claim-list">
          {claims.map((claim) => (
            <li key={claim.claim_id}>
              <button
                className={claim.claim_id === selectedId ? "selected" : ""}
                onClick={() => {
                  onSelect(claim.claim_id);
                }}
              >
                <span className="claim-list-top">
                  <code>{claim.claim_id}</code>
                  <span className={`status status-${claim.status}`}>
                    {labels[claim.status]}
                  </span>
                </span>
                <strong>{claim.summary}</strong>
                <span className="claim-list-meta">
                  {claim.claim_type.replaceAll("_", " ")}
                  <b>{formatMoney(claim.amount_claimed)}</b>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
