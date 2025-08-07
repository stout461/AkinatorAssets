import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { TestDataManager, UserCredentials } from '../utils/TestDataManager';

/**
 * Authentication test fixtures providing pre-configured page objects and test data
 */

// Extend the base test with authentication fixtures
export const test = base.extend<{
  loginPage: LoginPage;
  testCredentials: UserCredentials;
  multipleCredentials: UserCredentials[];
  invalidCredentials: UserCredentials;
}>({
  /**
   * LoginPage fixture - provides a configured LoginPage instance
   */
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  /**
   * Test credentials fixture - provides valid test user credentials
   */
  testCredentials: async ({}, use) => {
    const credentials = TestDataManager.getTestCredentials();
    await use(credentials);
  },

  /**
   * Multiple credentials fixture - provides array of test user credentials
   */
  multipleCredentials: async ({}, use) => {
    const credentials = TestDataManager.getMultipleTestCredentials();
    await use(credentials);
  },

  /**
   * Invalid credentials fixture - provides invalid credentials for error testing
   */
  invalidCredentials: async ({}, use) => {
    const invalidCreds: UserCredentials = {
      email: 'invalid@nonexistent.com',
      password: 'wrongpassword123',
      name: 'Invalid User'
    };
    await use(invalidCreds);
  }
});

/**
 * Authentication state fixtures for different test scenarios
 */
export const authFixtures = {
  /**
   * Set up a logged-in user state before test execution
   */
  loggedInUser: async (loginPage: LoginPage, credentials: UserCredentials) => {
    // Check if already logged in to avoid unnecessary login
    const isLoggedIn = await loginPage.isUserLoggedIn();
    
    if (!isLoggedIn) {
      await loginPage.navigateToLogin();
      await loginPage.login(credentials);
      await loginPage.verifyLoginSuccess();
    }
  },

  /**
   * Set up a logged-out user state before test execution
   */
  loggedOutUser: async (loginPage: LoginPage) => {
    // Navigate to logout endpoint to ensure clean state
    await loginPage.navigateTo('/logout');
    await loginPage.waitForPageLoad();
  },

  /**
   * Set up Auth0 mock responses for testing different scenarios
   */
  setupAuth0Mocks: async (page: any, scenario: 'success' | 'error' | 'timeout') => {
    switch (scenario) {
      case 'success':
        await page.route('**/auth/login', (route: any) => {
          route.fulfill({
            status: 302,
            headers: { 'Location': '/dashboard' }
          });
        });
        break;

      case 'error':
        await page.route('**/auth/login', (route: any) => {
          route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Invalid credentials' })
          });
        });
        break;

      case 'timeout':
        await page.route('**/auth/login', (route: any) => {
          // Simulate timeout by not responding
          setTimeout(() => {
            route.fulfill({
              status: 408,
              contentType: 'application/json',
              body: JSON.stringify({ error: 'Request timeout' })
            });
          }, 30000);
        });
        break;
    }
  }
};

/**
 * Authentication test data scenarios
 */
export const authTestData = {
  /**
   * Valid authentication scenarios
   */
  validScenarios: [
    {
      name: 'Standard user login',
      credentials: TestDataManager.getTestCredentials(),
      expectedRedirect: '/dashboard'
    }
  ],

  /**
   * Invalid authentication scenarios for error testing
   */
  invalidScenarios: [
    {
      name: 'Invalid email format',
      credentials: { email: 'invalid-email', password: 'password123' },
      expectedError: 'Invalid email format'
    },
    {
      name: 'Empty credentials',
      credentials: { email: '', password: '' },
      expectedError: 'Email and password are required'
    },
    {
      name: 'Wrong password',
      credentials: { email: 'test@example.com', password: 'wrongpassword' },
      expectedError: 'Invalid credentials'
    },
    {
      name: 'Non-existent user',
      credentials: { email: 'nonexistent@example.com', password: 'password123' },
      expectedError: 'User not found'
    }
  ],

  /**
   * Protected routes that require authentication
   */
  protectedRoutes: [
    '/dashboard',
    '/',
    '/detailed-graph/AAPL',
    '/api/moat-analysis'
  ],

  /**
   * Public routes that don't require authentication
   */
  publicRoutes: [
    '/login',
    '/auth/login',
    '/callback'
  ]
};

/**
 * Helper functions for authentication testing
 */
export const authHelpers = {
  /**
   * Verify that a user is redirected to login when accessing protected routes
   */
  verifyProtectedRouteRedirect: async (loginPage: LoginPage, route: string) => {
    await loginPage.navigateTo(route);
    
    // Should be redirected to login page
    const currentUrl = await loginPage.getCurrentUrl();
    expect(currentUrl).toContain('/login');
    
    // Login page should be displayed
    await loginPage.verifyLoginPageElements();
  },

  /**
   * Verify successful authentication flow
   */
  verifySuccessfulAuth: async (loginPage: LoginPage, credentials: UserCredentials) => {
    await loginPage.navigateToLogin();
    await loginPage.verifyLoginPageElements();
    await loginPage.login(credentials);
    await loginPage.verifyLoginSuccess();
  },

  /**
   * Verify failed authentication flow
   */
  verifyFailedAuth: async (loginPage: LoginPage, credentials: UserCredentials, expectedError?: string) => {
    await loginPage.navigateToLogin();
    await loginPage.clickLoginButton();
    await loginPage.fillAuth0Credentials(credentials);
    
    if (expectedError) {
      const errorMessage = await loginPage.waitForAuth0Error();
      expect(errorMessage).toContain(expectedError);
    }
  },

  /**
   * Clear browser session and cookies
   */
  clearSession: async (page: any) => {
    await page.context().clearCookies();
    
    // Only try to clear storage if we're on a page that allows it
    try {
      await page.evaluate(() => {
        if (typeof localStorage !== 'undefined') {
          localStorage.clear();
        }
        if (typeof sessionStorage !== 'undefined') {
          sessionStorage.clear();
        }
      });
    } catch (error) {
      // Ignore localStorage/sessionStorage errors - they might not be available
      console.log('Note: Could not clear browser storage (this is normal for some pages)');
    }
  },

  /**
   * Wait for authentication state to stabilize
   */
  waitForAuthState: async (loginPage: LoginPage, expectedState: 'logged_in' | 'logged_out') => {
    let attempts = 0;
    const maxAttempts = 10;
    
    while (attempts < maxAttempts) {
      const currentState = await loginPage.getAuthenticationState();
      
      if ((expectedState === 'logged_in' && currentState === 'logged_in') ||
          (expectedState === 'logged_out' && currentState === 'logged_out')) {
        return;
      }
      
      await loginPage.testPage.waitForTimeout(1000);
      attempts++;
    }
    
    throw new Error(`Authentication state did not stabilize to ${expectedState} within timeout`);
  }
};

// Export the expect function for use in tests
export { expect };