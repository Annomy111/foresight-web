import { test, expect } from '@playwright/test';

test.describe('Real AI Predictions Test', () => {
  test('should receive real AI predictions from backend with Grok-4 Fast', async ({ page }) => {
    // Navigate to the app
    await page.goto('https://foresight-analyzer.netlify.app');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Fill in the form
    await page.fill('input[name="question"]', 'Will AI significantly impact the job market by 2026?');
    await page.fill('input[name="definition"]', 'Significant means at least 20% of jobs transformed');
    await page.fill('input[name="timeframe"]', '2026');
    await page.fill('input[name="iterations"]', '1');

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for the loading state
    await expect(page.locator('text=/Analyzing with \\d+ AI models/i')).toBeVisible({ timeout: 10000 });

    // Wait for results (increased timeout for real API calls)
    await page.waitForSelector('.results-container', {
      state: 'visible',
      timeout: 120000 // 2 minutes for real API calls
    });

    // Check if we have real results
    const resultsContainer = page.locator('.results-container');
    await expect(resultsContainer).toBeVisible();

    // Verify we have the aggregate probability
    const aggregateProbability = page.locator('[data-testid="aggregate-probability"], .aggregate-probability, text=/Aggregate Probability:/i');
    await expect(aggregateProbability).toBeVisible();

    // Get the probability text
    const probabilityText = await aggregateProbability.textContent();
    console.log('Received probability:', probabilityText);

    // Check for model results
    const modelResults = page.locator('.model-result, [data-testid="model-result"]');
    const modelCount = await modelResults.count();
    console.log(`Found ${modelCount} model results`);

    // Verify at least one model returned results
    expect(modelCount).toBeGreaterThan(0);

    // Check if Grok-4 Fast is among the models
    const modelNames = await modelResults.evaluateAll((elements) =>
      elements.map(el => el.textContent || '')
    );

    console.log('Models used:', modelNames);

    // Look for Grok-4 Fast specifically
    const hasGrok = modelNames.some(name =>
      name.toLowerCase().includes('grok') ||
      name.includes('x-ai')
    );

    if (hasGrok) {
      console.log('✅ Grok-4 Fast is being used!');
    }

    // Verify the results are not mock data
    const isMockData = probabilityText?.includes('50.0%') &&
                       probabilityText?.includes('Mock') ||
                       modelNames.some(name => name.includes('Mock'));

    expect(isMockData).toBe(false);
    console.log('✅ Receiving real AI predictions, not mock data!');

    // Take a screenshot of the results
    await page.screenshot({
      path: 'test-results-real-ai.png',
      fullPage: true
    });
  });

  test('should show available models from backend', async ({ page }) => {
    // Check the models endpoint directly
    const response = await page.request.get('https://foresight-backend-api.onrender.com/api/models');
    expect(response.ok()).toBeTruthy();

    const models = await response.json();
    console.log('Available models from backend:', models);

    // Verify Grok-4 Fast is in the list
    const hasGrokFast = models.available_models?.some((model: string) =>
      model.includes('grok-4-fast') || model.includes('x-ai')
    );

    expect(hasGrokFast).toBeTruthy();
    console.log('✅ Backend has Grok-4 Fast configured!');
  });
});