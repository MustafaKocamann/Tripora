import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { claimDetail, queueClaim } from "./testFixtures";

function jsonResponse(data: object, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  } as Response;
}

function requestUrl(input: RequestInfo | URL) {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.toString();
  return input.url;
}

function installFetch(detail = claimDetail, actionStatus = 202) {
  const fetchMock = vi.fn(
    (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = requestUrl(input);
      if (url === "/api/claims" && !init)
        return Promise.resolve(
          jsonResponse({ claims: [queueClaim], total: 1 }),
        );
      if (url === "/api/agent/instructions")
        return Promise.resolve(
          jsonResponse({ instructions: "Decide from policy wording." }),
        );
      if (url === "/api/claims/CLM-1001" && !init)
        return Promise.resolve(jsonResponse(detail));
      return Promise.resolve(jsonResponse({ status: "started" }, actionStatus));
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows loading and then the queue with full claim detail", async () => {
    installFetch();
    render(<App />);
    expect(screen.getByText("Loading claims…")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: queueClaim.summary }),
    ).toBeVisible();
    expect(screen.getByText("Maya Patel")).toBeVisible();
    expect(screen.getByText("Cancellation notice")).toBeVisible();
    expect(screen.getByText("Bag arrived late")).toBeVisible();
  });

  it("shows read-only instructions", async () => {
    installFetch();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole("heading", { name: queueClaim.summary });
    await user.click(
      screen.getByRole("button", { name: "Agent instructions" }),
    );
    expect(screen.getByText("Decide from policy wording.")).toBeVisible();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Claims" }));
    expect(
      screen.getByRole("heading", { name: queueClaim.summary }),
    ).toBeVisible();
  });

  it("starts a waiting claim with the dedicated run operation", async () => {
    const fetchMock = installFetch();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole("heading", { name: queueClaim.summary });
    await user.click(screen.getByRole("button", { name: "Run agent" }));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/claims/CLM-1001/runs",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("polls while a claim is in progress", async () => {
    const timer = vi.spyOn(window, "setInterval");
    installFetch({ ...claimDetail, status: "in_progress" });
    const { unmount } = render(<App />);
    await screen.findByRole("heading", { name: queueClaim.summary });
    expect(timer).toHaveBeenCalled();
    unmount();
  });

  it("uses separate sign-off and payment operations", async () => {
    const highValue = {
      ...claimDetail,
      status: "waiting_for_sign_off" as const,
      decision: {
        decision: "approve" as const,
        payout: 1250,
        rationale: "Covered by Section 3.",
        policy_section: "Section 3",
      },
    };
    const signOffFetch = installFetch(highValue);
    const user = userEvent.setup();
    const { unmount } = render(<App />);
    await screen.findByRole("button", { name: "Sign off payout" });
    await user.click(screen.getByRole("button", { name: "Sign off payout" }));
    await waitFor(() => {
      expect(signOffFetch).toHaveBeenCalledWith(
        "/api/claims/CLM-1001/sign-offs",
        expect.objectContaining({ method: "POST" }),
      );
    });
    unmount();

    const signed = {
      ...highValue,
      status: "decided" as const,
      sign_off: { handler_id: "HND-01", signed_at: "2026-01-01" },
    };
    const paymentFetch = installFetch(signed);
    render(<App />);
    await screen.findByRole("button", { name: "Record payment" });
    await user.click(screen.getByRole("button", { name: "Record payment" }));
    await waitFor(() => {
      expect(paymentFetch).toHaveBeenCalledWith(
        "/api/claims/CLM-1001/payments",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("shows an action error without losing the claim", async () => {
    installFetch(claimDetail, 409);
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole("button", { name: "Run agent" });
    await user.click(screen.getByRole("button", { name: "Run agent" }));
    expect(await screen.findByText("Request failed with 409")).toBeVisible();
    expect(
      screen.getByRole("heading", { name: queueClaim.summary }),
    ).toBeVisible();
  });

  it("shows request errors and an empty queue", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(jsonResponse({}, 500))),
    );
    render(<App />);
    expect(await screen.findByText("Request failed with 500")).toBeVisible();
    expect(screen.getByText("No claims in the queue.")).toBeVisible();
    expect(screen.getByText("Select a claim.")).toBeVisible();
  });
});
