import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { queueClaim } from "../testFixtures";
import { formatMoney } from "../format";
import { Queue } from "./Queue";

describe("Queue", () => {
  it("shows an empty state", () => {
    render(<Queue claims={[]} selectedId={null} onSelect={vi.fn()} />);
    expect(screen.getByText("No claims in the queue.")).toBeVisible();
  });

  it("shows every state and selects a claim", async () => {
    const onSelect = vi.fn();
    const claims = [
      queueClaim,
      { ...queueClaim, claim_id: "CLM-2", status: "in_progress" as const },
      {
        ...queueClaim,
        claim_id: "CLM-3",
        status: "waiting_for_sign_off" as const,
      },
      { ...queueClaim, claim_id: "CLM-4", status: "decided" as const },
    ];
    render(<Queue claims={claims} selectedId="CLM-2" onSelect={onSelect} />);
    expect(screen.getByText("Waiting")).toBeVisible();
    expect(screen.getByText("In progress")).toBeVisible();
    expect(screen.getByText("Waiting for sign-off")).toBeVisible();
    expect(screen.getByText("Decided")).toBeVisible();
    expect(screen.getAllByText("$420.00")).toHaveLength(4);
    await userEvent.click(screen.getByRole("button", { name: /CLM-4/ }));
    expect(onSelect).toHaveBeenCalledWith("CLM-4");
  });

  it("formats US dollars", () => {
    expect(formatMoney(1250)).toBe("$1,250.00");
  });
});
