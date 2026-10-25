import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { claimDetail } from "../testFixtures";
import { ClaimDetailPanel } from "./ClaimDetailPanel";

const actions = {
  onRun: vi.fn(),
  onSignOff: vi.fn(),
  onPay: vi.fn(),
};

describe("ClaimDetailPanel", () => {
  it("asks the handler to select a claim", () => {
    render(<ClaimDetailPanel detail={null} busy={false} {...actions} />);
    expect(screen.getByText("Select a claim.")).toBeVisible();
  });

  it("runs a waiting claim and shows empty activity", async () => {
    render(<ClaimDetailPanel detail={claimDetail} busy={false} {...actions} />);
    await userEvent.click(screen.getByRole("button", { name: "Run agent" }));
    expect(actions.onRun).toHaveBeenCalled();
    expect(screen.getByText("No agent activity yet.")).toBeVisible();
  });

  it("shows decision, activity and sign-off control", async () => {
    const detail = {
      ...claimDetail,
      status: "waiting_for_sign_off" as const,
      decision: {
        decision: "approve" as const,
        payout: 1250,
        rationale: "Covered by the cancellation terms.",
        policy_section: "Section 3",
      },
      activities: [
        {
          activity_id: 1,
          step: "decision",
          message: "Decision recorded: approve",
          created_at: "2026-01-01",
        },
      ],
    };
    render(<ClaimDetailPanel detail={detail} busy={false} {...actions} />);
    expect(screen.getByText("$1,250.00")).toBeVisible();
    expect(screen.getByText("Decision recorded: approve")).toBeVisible();
    await userEvent.click(
      screen.getByRole("button", { name: "Sign off payout" }),
    );
    expect(actions.onSignOff).toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Record payment" })).toBeNull();
  });

  it("offers a separate payment after sign-off", async () => {
    const detail = {
      ...claimDetail,
      status: "decided" as const,
      decision: {
        decision: "approve" as const,
        payout: 1250,
        rationale: "Covered by the cancellation terms.",
        policy_section: "Section 3",
      },
      sign_off: { handler_id: "HND-01", signed_at: "2026-01-01" },
    };
    render(<ClaimDetailPanel detail={detail} busy={false} {...actions} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Record payment" }),
    );
    expect(actions.onPay).toHaveBeenCalled();
  });

  it("shows no previous-claim state and disables a busy action", () => {
    const detail = {
      ...claimDetail,
      customer: { ...claimDetail.customer, previous_claims: [] },
    };
    render(<ClaimDetailPanel detail={detail} busy {...actions} />);
    expect(screen.getByText("No previous claims.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Run agent" })).toBeDisabled();
  });
});
