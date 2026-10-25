import type { ClaimDetail, InstructionsResponse, QueueResponse } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok)
    throw new Error(`Request failed with ${String(response.status)}`);
  return (await response.json()) as T;
}

const jsonHeaders = { "Content-Type": "application/json" };

export function getClaims() {
  return request<QueueResponse>("/api/claims");
}

export function getClaim(claimId: string) {
  return request<ClaimDetail>(`/api/claims/${claimId}`);
}

export function getInstructions() {
  return request<InstructionsResponse>("/api/agent/instructions");
}

export function startClaim(claimId: string, threadId: string) {
  return request(`/api/claims/${claimId}/runs`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ thread_id: threadId }),
  });
}

export function signOffClaim(claimId: string, handlerId: string) {
  return request(`/api/claims/${claimId}/sign-offs`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ handler_id: handlerId }),
  });
}

export function payClaim(claimId: string, amount: number) {
  return request(`/api/claims/${claimId}/payments`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ amount }),
  });
}
