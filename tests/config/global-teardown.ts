import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Running global test teardown...');

  // Clean up any global resources if needed
  // This is where you would close databases, stop servers, etc.

  console.log('✅ Global teardown completed');
}

export default globalTeardown;