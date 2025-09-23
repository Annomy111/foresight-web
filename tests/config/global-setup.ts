import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up global test environment...');

  // Launch browser to warm up
  const browser = await chromium.launch();

  // Check if the target URL is accessible
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'https://foresight-analyzer.netlify.app';
    console.log(`🌐 Testing connectivity to: ${baseURL}`);

    await page.goto(baseURL, { timeout: 30000 });
    await page.waitForLoadState('networkidle');

    console.log('✅ Application is accessible');
  } catch (error) {
    console.warn('⚠️ Application might not be accessible:', (error as Error).message);
  } finally {
    await context.close();
    await browser.close();
  }

  console.log('✅ Global setup completed');
}

export default globalSetup;