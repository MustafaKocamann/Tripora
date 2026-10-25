import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

interface BrowserErrors {
  console: string[];
  api: string[];
}

interface PrivateClaim {
  customer: {
    customer_id: string;
    name: string;
    email: string;
    phone: string;
    date_of_birth: string;
    address: Record<string, string>;
  };
  policy: { travelers: string[] };
}

const decisionCard = (page: Page) => page.locator(".decision-card");

function monitorBrowser(page: Page): BrowserErrors {
  const errors: BrowserErrors = { console: [], api: [] };
  page.on("console", (message) => {
    if (message.type() === "error") errors.console.push(message.text());
  });
  page.on("response", (response) => {
    if (response.url().includes("/api/") && !response.ok()) {
      errors.api.push(`${String(response.status())} ${response.url()}`);
    }
  });
  return errors;
}

function collectKeys(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(collectKeys);
  if (typeof value !== "object" || value === null) return [];
  return Object.entries(value).flatMap(([key, child]) => [
    key,
    ...collectKeys(child),
  ]);
}

async function openDashboard(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "UnderCover" })).toBeVisible();
}

async function selectClaim(page: Page, claimId: string) {
  const queueButton = page.getByRole("button", {
    name: new RegExp(claimId),
  });
  await queueButton.click();
  await expect(queueButton).toHaveClass(/selected/);
  return queueButton;
}

async function runClaim(page: Page, decision: string, payout: string) {
  await page.getByRole("button", { name: "Run agent" }).click();
  await expect(decisionCard(page)).toContainText(decision, { timeout: 15_000 });
  await expect(decisionCard(page)).toContainText(payout);
  await expect(page.getByText(`Decision recorded: ${decision}`)).toBeVisible();
}

test("approves a claim, records payment and preserves the result", async ({
  page,
}) => {
  const errors = monitorBrowser(page);
  const browserPosts: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST") {
      browserPosts.push(new URL(request.url()).pathname);
    }
  });

  await openDashboard(page);
  const queueButton = await selectClaim(page, "CLM-1001");
  await runClaim(page, "approve", "$420.00");
  await expect(queueButton).toContainText("Decided");
  await expect(page.getByText("Simulated payment recorded")).toBeVisible();
  expect(browserPosts).toEqual(["/api/claims/CLM-1001/runs"]);

  await page.reload();
  await expect(decisionCard(page)).toContainText("approve");
  await expect(decisionCard(page)).toContainText("Section 2");
  await expect(page.getByText("Simulated payment recorded")).toBeVisible();
  expect(errors).toEqual({ console: [], api: [] });
});

test("declines a claim with a zero payout and stored reasons", async ({
  page,
}) => {
  const errors = monitorBrowser(page);
  await openDashboard(page);
  await selectClaim(page, "CLM-1002");
  await runClaim(page, "decline", "$0.00");
  await expect(decisionCard(page)).toContainText("Section 6");
  await expect(
    page.getByRole("button", { name: "Record payment" }),
  ).toHaveCount(0);

  await page.reload();
  await selectClaim(page, "CLM-1002");
  await expect(decisionCard(page)).toContainText("decline");
  expect(errors).toEqual({ console: [], api: [] });
});

test("refers a claim with a zero payout and stored reasons", async ({
  page,
}) => {
  const errors = monitorBrowser(page);
  await openDashboard(page);
  await selectClaim(page, "CLM-1003");
  await runClaim(page, "refer", "$0.00");
  await expect(decisionCard(page)).toContainText("Section 8");
  await expect(
    page.getByRole("button", { name: "Record payment" }),
  ).toHaveCount(0);
  expect(errors).toEqual({ console: [], api: [] });
});

test("blocks a high-value payment until separate handler sign-off", async ({
  page,
  request,
}) => {
  const errors = monitorBrowser(page);
  await openDashboard(page);
  const queueButton = await selectClaim(page, "CLM-1008");
  await runClaim(page, "approve", "$1,250.00");
  await expect(queueButton).toContainText("Waiting for sign-off");
  await expect(
    page.getByText("Payment is waiting for handler sign-off"),
  ).toBeVisible();

  const blocked = await request.post("/api/claims/CLM-1008/payments", {
    data: { amount: 1250 },
  });
  expect(blocked.status()).toBe(409);
  expect(await blocked.json()).toEqual({ detail: "Handler sign-off required" });

  await page.reload();
  await selectClaim(page, "CLM-1008");
  await expect(decisionCard(page)).toContainText("Section 3");
  await page.getByRole("button", { name: "Sign off payout" }).click();
  await expect(page.getByText("Handler sign-off recorded")).toBeVisible();
  await page.getByRole("button", { name: "Record payment" }).click();
  await expect(page.getByText("Simulated payment recorded")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record payment" }),
  ).toHaveCount(0);

  await page.reload();
  await selectClaim(page, "CLM-1008");
  await expect(decisionCard(page)).toContainText("approve");
  await expect(page.getByText("Handler sign-off recorded")).toBeVisible();
  await expect(page.getByText("Simulated payment recorded")).toBeVisible();
  expect(errors).toEqual({ console: [], api: [] });
});

test("agent context excludes every customer and traveler identity field and value", async ({
  request,
}) => {
  const fullResponse = await request.get("/api/claims/CLM-1001");
  const contextResponse = await request.get(
    "/api/agent/claims/CLM-1001/context",
  );
  expect(fullResponse.ok()).toBe(true);
  expect(contextResponse.ok()).toBe(true);

  const full = (await fullResponse.json()) as PrivateClaim;
  const context = (await contextResponse.json()) as unknown;
  const forbiddenFields = [
    "name",
    "customer_id",
    "email",
    "phone",
    "address",
    "date_of_birth",
    "travelers",
  ];
  const contextKeys = collectKeys(context);
  expect(contextKeys.filter((key) => forbiddenFields.includes(key))).toEqual(
    [],
  );

  const forbiddenValues = [
    full.customer.customer_id,
    full.customer.name,
    full.customer.email,
    full.customer.phone,
    full.customer.date_of_birth,
    ...Object.values(full.customer.address),
    ...full.policy.travelers,
  ].filter((value) => value.length >= 4);
  const serializedContext = JSON.stringify(context).toLowerCase();
  expect(
    forbiddenValues.filter((value) =>
      serializedContext.includes(value.toLowerCase()),
    ),
  ).toEqual([]);
  expect(serializedContext).toContain("[redacted]");
});
