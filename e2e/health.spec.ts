import { expect, test } from "@playwright/test";

test("loads the UnderCover dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "UnderCover" })).toBeVisible();
});
