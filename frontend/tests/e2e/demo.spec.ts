import { expect, test } from "@playwright/test";

test("demo route enters demo mode and opens the sample guide", async ({ context, page }) => {
  await page.goto("/demo");

  await page.waitForURL("**/guide/demo-guide-001");

  await expect(
    page.getByRole("heading", {
      name: /but what is a neural network\?/i,
    })
  ).toBeVisible();
  await expect(page.getByText("Key Themes")).toBeVisible();
  await expect(page.getByText("Active Recall Quiz")).toBeVisible();
  await expect(page.getByText("Reflect & Internalize")).toBeVisible();

  const cookies = await context.cookies();
  expect(cookies.some((cookie) => cookie.name === "mindmesh-demo" && cookie.value === "true")).toBeTruthy();
});

test("landing page demo CTA reaches the guided demo experience", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Try Demo" }).first().click();

  await page.waitForURL("**/guide/demo-guide-001");
  await expect(page.getByRole("button", { name: /back to library/i })).toBeVisible();
});