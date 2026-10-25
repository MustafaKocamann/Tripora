import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getClaim,
  getClaims,
  getInstructions,
  payClaim,
  signOffClaim,
  startClaim,
} from "./api";

function response(data: object, ok = true): Response {
  return {
    ok,
    status: ok ? 200 : 409,
    json: () => Promise.resolve(data),
  } as Response;
}

afterEach(() => vi.unstubAllGlobals());

describe("API client", () => {
  it("uses the read endpoints", async () => {
    const fetchMock = vi.fn<typeof fetch>(() =>
      Promise.resolve(response({ value: true })),
    );
    vi.stubGlobal("fetch", fetchMock);
    await getClaims();
    await getClaim("CLM-1001");
    await getInstructions();
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      "/api/claims",
      "/api/claims/CLM-1001",
      "/api/agent/instructions",
    ]);
  });

  it("uses separate run, sign-off and payment operations", async () => {
    const fetchMock = vi.fn<typeof fetch>(() =>
      Promise.resolve(response({ value: true })),
    );
    vi.stubGlobal("fetch", fetchMock);
    await startClaim("CLM-1001", "thread-1");
    await signOffClaim("CLM-1001", "HND-01");
    await payClaim("CLM-1001", 1250);
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      "/api/claims/CLM-1001/runs",
      "/api/claims/CLM-1001/sign-offs",
      "/api/claims/CLM-1001/payments",
    ]);
    expect(fetchMock.mock.calls[2]?.[1]?.body).toBe('{"amount":1250}');
  });

  it("throws a status-based error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(response({}, false))),
    );
    await expect(getClaims()).rejects.toThrow("Request failed with 409");
  });
});
