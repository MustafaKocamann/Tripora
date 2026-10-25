import type { ClaimDetail, QueueClaim } from "./types";

export const queueClaim: QueueClaim = {
  claim_id: "CLM-1001",
  claim_type: "trip_delay",
  summary: "Flight canceled overnight",
  submitted_on: "2026-06-24",
  amount_claimed: 420,
  status: "waiting",
  decision: null,
  payout: null,
};

export const claimDetail: ClaimDetail = {
  claim: {
    claim_id: "CLM-1001",
    claim_type: "trip_delay",
    submitted_on: "2026-06-24",
    incident_date: "2026-06-18",
    incident_location: "Rome, Italy",
    summary: "Flight canceled overnight",
    story: "The airline canceled the flight and rebooked it the next morning.",
    amount_claimed: 420,
    items: [
      { description: "Airport hotel", category: "accommodation", amount: 245 },
    ],
    documents: [
      {
        name: "Cancellation notice",
        type: "carrier_report",
        content: "The flight was canceled because of crew availability.",
      },
    ],
  },
  customer: {
    name: "Maya Patel",
    email: "maya@example.com",
    phone: "+1 555 0100",
    date_of_birth: "1988-03-14",
    address: {
      street: "48 Wayne Street",
      city: "Jersey City",
      state: "NJ",
      zip: "07302",
    },
    previous_claims: [
      {
        claim_id: "CLM-0412",
        claim_type: "baggage_delay",
        summary: "Bag arrived late",
        outcome: "approved",
        amount_paid: 140,
      },
    ],
  },
  policy: {
    plan: "premium",
    add_ons: [],
    status: "active",
    trip: {
      destination: "Rome, Italy",
      departs_on: "2026-06-10",
      returns_on: "2026-06-18",
      trip_cost: 3100,
    },
  },
  plan: {},
  status: "waiting",
  decision: null,
  activities: [],
  sign_off: null,
  payment: null,
};
