import { expect, test } from "@playwright/test";

test("loads the branded handler dashboard and read-only instructions", async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  const apiErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.url().includes("/api/") && !response.ok()) {
      apiErrors.push(`${String(response.status())} ${response.url()}`);
    }
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "UnderCover" })).toBeVisible();
  await expect(page.getByText("25", { exact: true })).toBeVisible();
  await expect(page.getByText("$420.00").first()).toBeVisible();

  await page.getByRole("button", { name: "Agent instructions" }).click();
  await expect(
    page.getByRole("heading", { name: "Agent instructions" }),
  ).toBeVisible();
  await expect(page.getByRole("textbox")).toHaveCount(0);
  await page.getByRole("button", { name: "Claims" }).click();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Claims", exact: true }),
  ).toBeVisible();
  expect(consoleErrors).toEqual([]);
  expect(apiErrors).toEqual([]);
});
