import { expect, test } from "@playwright/test";

test("loads the branded handler dashboard and runs a claim", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "UnderCover" })).toBeVisible();
  await expect(page.getByText("25", { exact: true })).toBeVisible();
  await expect(page.getByText("$420.00").first()).toBeVisible();

  await page.getByRole("button", { name: "Agent instructions" }).click();
  await expect(page.getByRole("heading", { name: "Agent instructions" })).toBeVisible();
  await expect(page.getByRole("textbox")).toHaveCount(0);
  await page.getByRole("button", { name: "Claims" }).click();

  await page.getByRole("button", { name: "Run agent" }).click();
  await expect(page.getByText("approve", { exact: true })).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText("Decision recorded: approve")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Claims", exact: true }),
  ).toBeVisible();
  expect(consoleErrors).toEqual([]);
});
