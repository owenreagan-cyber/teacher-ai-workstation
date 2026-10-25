// Isolated headless UI acceptance tests for the Weekly Planner Agent surface.
// Runs against a local fixture server (127.0.0.1:4311); never touches Canvas
// and never drives Owen's visible desktop.
// @ts-check
const { test, expect } = require('@playwright/test');

async function openAgent(page) {
  await page.goto('/#agent');
  await expect(page.locator('#agent-tabs')).toBeVisible();
  return page;
}

async function openTab(page, tab) {
  await page.locator(`.agent-tab[data-agent-tab="${tab}"]`).click();
  await expect(page.locator('#agent-body')).not.toContainText('Loading…');
}

test.describe('Weekly Planner Agent UI', () => {
  test('Today loads and shows assessment-date watch', async ({ page }) => {
    await openAgent(page);
    await expect(page.locator('#agent-body h2')).toContainText('Today');
    await expect(page.locator('#agent-body')).toContainText('Assessment date watch');
    await expect(page.locator('#agent-body')).toContainText('Source freshness');
  });

  test('Assessment Date Watch renders old/new dates and affected artifacts', async ({ page }) => {
    await openAgent(page);
    await expect(page.locator('.watch-card')).toBeVisible();
    await expect(page.locator('.watch-card .old')).toContainText('2026-11-05');
    await expect(page.locator('.watch-card .new')).toContainText('2026-11-06');
    await expect(page.locator('.watch-card')).toContainText('Written Assessment 8');
    await expect(page.locator('.watch-card')).toContainText('weekly page');
    await expect(page.locator('.watch-card')).toContainText('assignment');
    await expect(page.locator('.watch-card')).toContainText('Would you like me to prepare the updated Canvas items');
  });

  test('Week Plan loads and distinguishes predicted items', async ({ page }) => {
    await openAgent(page);
    await openTab(page, 'week-plan');
    await expect(page.locator('#agent-body h2')).toContainText('Week plan');
    // Predicted science day is visibly distinguished.
    await expect(page.locator('.agent-subject-grid')).toContainText('Predicted — suggested');
    // Confirmed math days are marked confirmed.
    await expect(page.locator('.agent-subject-grid')).toContainText('Confirmed');
  });

  test('Changes card renders with source and old→new', async ({ page }) => {
    await openAgent(page);
    await openTab(page, 'changes');
    await expect(page.locator('#agent-body')).toContainText('What changed');
    await expect(page.locator('.change-card:not(.watch-card)')).toBeVisible();
    await expect(page.locator('.change-card:not(.watch-card)')).toContainText('Source');
  });

  test('Friday Review renders with blockers and approval disabled', async ({ page }) => {
    await openAgent(page);
    await openTab(page, 'friday-review');
    await expect(page.locator('#agent-body h2')).toContainText('Friday review');
    await expect(page.locator('#agent-body')).toContainText('Homeroom items');
    await expect(page.locator('#agent-body')).toContainText('Email delivery');
    // Blocked state: no approve button when blockers exist.
    await expect(page.locator('[data-agent-approve]')).toHaveCount(0);
  });

  test('Agent chat: raw technical fields hidden until Advanced opened', async ({ page }) => {
    await openAgent(page);
    await openTab(page, 'agent');
    await expect(page.locator('#agent-input')).toBeVisible();
    const advanced = page.locator('.agent-advanced');
    const raw = advanced.locator('pre');
    // Raw plan JSON is hidden by default (details collapsed).
    await expect(raw).toBeHidden();
    // Opening Advanced reveals the technical details.
    await advanced.locator('summary').click();
    await expect(raw).toBeVisible();
    await expect(raw).toContainText('Q2W3');
  });

  test('Plain-language edit changes the proposed plan', async ({ page }) => {
    await openAgent(page);
    await openTab(page, 'agent');
    await page.fill('#agent-input', 'No Science homework this week.');
    await page.locator('#agent-form button[type="submit"]').click();
    await expect(page.locator('.agent-conversation')).toContainText('homework', { timeout: 5000 });
  });

  test('Teacher override persists after a plain-language keep', async ({ page }) => {
    await openAgent(page);
    await openTab(page, 'agent');
    await page.fill('#agent-input', 'Keep the Math test Thursday.');
    await page.locator('#agent-form button[type="submit"]').click();
    await expect(page.locator('.agent-conversation')).toContainText('override', { timeout: 5000 });
    // Override is persisted and visible in the Week plan.
    await openTab(page, 'week-plan');
    await expect(page.locator('.agent-day').filter({ hasText: 'Your override' })).toBeVisible();
  });

  test('Route protection: unauthenticated write is rejected', async ({ request }) => {
    const res = await request.post('/api/agent/instruct/2/3', {
      data: { text: 'Move the Math test to Friday.' },
    });
    expect(res.status()).toBe(403);
  });
});
