export type ClaimStatus =
  "waiting" | "in_progress" | "waiting_for_sign_off" | "decided";

export type DecisionValue = "approve" | "decline" | "refer";

export interface QueueClaim {
  claim_id: string;
  claim_type: string;
  summary: string;
  submitted_on: string;
  amount_claimed: number;
  status: ClaimStatus;
  decision: DecisionValue | null;
  payout: number | null;
}

export interface QueueResponse {
  claims: QueueClaim[];
  total: number;
}

export interface ClaimItem {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface ClaimRecord {
  claim_id: string;
  claim_type: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: ClaimItem[];
  amount_claimed: number;
  documents: ClaimDocument[];
}

export interface CustomerRecord {
  name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  address: { street: string; city: string; state: string; zip: string };
  previous_claims: {
    claim_id: string;
    claim_type: string;
    summary: string;
    outcome: string;
    amount_paid: number;
  }[];
}

export interface PolicyRecord {
  plan: string;
  add_ons: string[];
  status: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
}

export interface Activity {
  activity_id: number;
  step: string;
  message: string;
  created_at: string;
}

export interface Decision {
  decision: DecisionValue;
  payout: number;
  rationale: string;
  policy_section: string;
}

export interface ClaimDetail {
  claim: ClaimRecord;
  customer: CustomerRecord;
  policy: PolicyRecord;
  plan: Record<string, unknown>;
  status: ClaimStatus;
  decision: Decision | null;
  activities: Activity[];
  sign_off: { handler_id: string; signed_at: string } | null;
  payment: { amount: number; recorded_at: string } | null;
}

export interface InstructionsResponse {
  instructions: string;
}
