import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { TestDataManager } from '../utils/TestDataManager';

/**
 * Fast authentication fixtures that reuse stored auth state
 * This avoids logging in for every test, significantly speeding up test execution
 */

type FastAuthFixtures = {
  authenticatedPage: any;
  testCredentials: { email: string; password: string; name?: string };
};

export const test = base.extend<FastAuthFixtures>({
  // Use stored authentication state instead of logging in each time
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: 'tests/auth-state.json'
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  testCredentials: async ({}, use) => {
    const credentials = TestDataManager.getTestCredentials();
    await use(credentials);
  },
});

export { expect };