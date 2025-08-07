import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { UserCredentials } from '../utils/TestDataManager';

/**
 * Page Object Model for the Login page
 * Handles Auth0 integration and authentication flows
 */
export class LoginPage extends BasePage {
  // Main login page selectors
  private readonly loginContainer: Locator;
  private readonly loginButton: Locator;
  private readonly logoTitle: Locator;
  private readonly welcomeText: Locator;
  private readonly securityBadge: Locator;
  private readonly featureList: Locator;

  // Auth0 specific selectors (will appear after clicking login)
  private readonly auth0Container: Locator;
  private readonly auth0EmailInput: Locator;
  private readonly auth0PasswordInput: Locator;
  private readonly auth0SubmitButton: Locator;
  private readonly auth0ErrorMessage: Locator;
  private readonly auth0LoadingSpinner: Locator;

  // Expose page for test access
  get testPage(): Page {
    return this.page;
  }

  constructor(page: Page) {
    super(page);
    
    // Initialize main login page selectors
    this.loginContainer = page.locator('.login-container');
    this.loginButton = page.locator('.login-button');
    this.logoTitle = page.locator('.logo h1');
    this.welcomeText = page.locator('.welcome-text h2');
    this.securityBadge = page.locator('.security-badge');
    this.featureList = page.locator('.feature-list');

    // Initialize Auth0 selectors (these will be available after redirect)
    this.auth0Container = page.locator('[data-testid="auth0-lock-container"], .auth0-lock-widget, #auth0-lock-container');
    this.auth0EmailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]');
    this.auth0PasswordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password" i]');
    this.auth0SubmitButton = page.locator('button[type="submit"], .auth0-lock-submit, button:has-text("Log In"), button:has-text("Continue")');
    this.auth0ErrorMessage = page.locator('.auth0-lock-error-msg, .error-message, [data-testid="error"]');
    this.auth0LoadingSpinner = page.locator('.auth0-loading, .loading-spinner, .spinner');
  }

  /**
   * Wait for the login page to fully load
   */
  async waitForPageLoad(): Promise<void> {
    await this.waitForElement(this.loginContainer);
    await this.waitForElement(this.loginButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Navigate to the login page
   */
  async navigateToLogin(): Promise<void> {
    await this.navigateTo('/login');
  }

  /**
   * Click the main login button to initiate Auth0 flow
   */
  async clickLoginButton(): Promise<void> {
    await this.waitForElement(this.loginButton);
    await this.clickAndWaitForNavigation(this.loginButton);
  }

  /**
   * Wait for Auth0 redirect and form to appear
   */
  async waitForAuth0Redirect(): Promise<void> {
    // Wait for URL to change to Auth0 domain or callback
    await this.page.waitForFunction(() => {
      return window.location.href.includes('auth0') || 
             window.location.href.includes('/callback') ||
             window.location.href.includes('/auth/login');
    }, { timeout: 10000 });

    // Wait for Auth0 form elements to be available
    try {
      await this.waitForElement(this.auth0EmailInput, 5000);
    } catch {
      // If Auth0 form doesn't appear, it might be auto-login or different flow
      console.log('Auth0 form not detected, checking for alternative flows');
    }
  }

  /**
   * Fill in Auth0 credentials and submit
   * @param credentials - User credentials for authentication
   */
  async fillAuth0Credentials(credentials: UserCredentials): Promise<void> {
    // Wait for Auth0 form to be ready
    await this.waitForAuth0Redirect();

    // Use more specific selectors that we know work
    const emailInput = this.page.locator('input[type="email"], input[name="email"], input[name="username"]').first();
    const passwordInput = this.page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = this.page.locator('button[type="submit"], button:has-text("Continue")').first();
    
    // Check if we need to fill credentials or if it's auto-login
    const emailVisible = await emailInput.isVisible();
    
    if (emailVisible) {
      await emailInput.fill(credentials.email);
      await passwordInput.fill(credentials.password);
      
      // Submit the form and wait for navigation
      await submitButton.click();
      
      // Wait for redirect back to application
      await this.page.waitForTimeout(3000);
    }
  }

  /**
   * Complete the full login process
   * @param credentials - User credentials for authentication
   */
  async login(credentials: UserCredentials): Promise<void> {
    await this.clickLoginButton();
    await this.fillAuth0Credentials(credentials);
    await this.waitForLoginSuccess();
  }

  /**
   * Wait for successful login and redirect to dashboard
   */
  async waitForLoginSuccess(): Promise<void> {
    // Wait for redirect to dashboard or main application
    await this.page.waitForFunction(() => {
      return window.location.pathname === '/dashboard' || 
             window.location.pathname === '/' ||
             (!window.location.href.includes('auth0') && window.location.hostname === 'localhost');
    }, { timeout: 30000 });

    // Wait for dashboard elements to be available
    await this.page.waitForFunction(() => {
      return document.querySelector('#ticker') !== null;
    }, { timeout: 15000 });

    // Wait for page to load completely
    await this.waitForLoadingToComplete();
  }

  /**
   * Verify that login was successful by checking for dashboard elements
   */
  async verifyLoginSuccess(): Promise<void> {
    const currentUrl = await this.getCurrentUrl();
    
    // Should be redirected away from login page
    expect(currentUrl).not.toContain('/login');
    
    // Should be on dashboard or main page
    expect(currentUrl).toMatch(/\/(dashboard|$)/);

    // Wait for authenticated content to load
    await this.waitForLoadingToComplete();
  }

  /**
   * Verify login page elements are displayed correctly
   */
  async verifyLoginPageElements(): Promise<void> {
    // Check main container is visible
    await expect(this.loginContainer).toBeVisible();
    
    // Check logo and title
    await expect(this.logoTitle).toBeVisible();
    await expect(this.logoTitle).toContainText('Akinator Assets');
    
    // Check welcome text
    await expect(this.welcomeText).toBeVisible();
    await expect(this.welcomeText).toContainText('Welcome Back!');
    
    // Check login button
    await expect(this.loginButton).toBeVisible();
    await expect(this.loginButton).toContainText('Continue with Auth0');
    
    // Check security badge
    await expect(this.securityBadge).toBeVisible();
    await expect(this.securityBadge).toContainText('Secured by Auth0');
    
    // Check feature list
    await expect(this.featureList).toBeVisible();
  }

  /**
   * Check if user is already logged in by checking session
   */
  async isUserLoggedIn(): Promise<boolean> {
    try {
      // Try to navigate to a protected route
      await this.navigateTo('/dashboard');
      
      // If we're not redirected to login, user is logged in
      const currentUrl = await this.getCurrentUrl();
      return !currentUrl.includes('/login');
    } catch {
      return false;
    }
  }

  /**
   * Wait for and capture Auth0 error message
   */
  async waitForAuth0Error(): Promise<string> {
    await this.waitForElement(this.auth0ErrorMessage);
    return await this.getElementText(this.auth0ErrorMessage);
  }

  /**
   * Verify Auth0 form elements are present
   */
  async verifyAuth0FormElements(): Promise<void> {
    await this.waitForAuth0Redirect();
    
    const emailVisible = await this.isElementVisible(this.auth0EmailInput);
    if (emailVisible) {
      await expect(this.auth0EmailInput).toBeVisible();
      await expect(this.auth0PasswordInput).toBeVisible();
      await expect(this.auth0SubmitButton).toBeVisible();
    }
  }

  /**
   * Get the current authentication state from the page
   */
  async getAuthenticationState(): Promise<'logged_out' | 'logging_in' | 'logged_in' | 'error'> {
    const currentUrl = await this.getCurrentUrl();
    
    if (currentUrl.includes('/login')) {
      return 'logged_out';
    } else if (currentUrl.includes('auth0') || currentUrl.includes('/callback')) {
      return 'logging_in';
    } else if (currentUrl.includes('/dashboard') || currentUrl === this.baseURL + '/') {
      return 'logged_in';
    } else {
      return 'error';
    }
  }

  /**
   * Wait for loading spinner to disappear during Auth0 flow
   */
  async waitForAuth0Loading(): Promise<void> {
    try {
      await this.waitForElement(this.auth0LoadingSpinner, 2000);
      await this.page.waitForSelector('.auth0-loading, .loading-spinner, .spinner', { 
        state: 'hidden', 
        timeout: 10000 
      });
    } catch {
      // Loading spinner might not appear for fast responses
    }
  }

  /**
   * Handle different Auth0 authentication scenarios
   * @param credentials - User credentials
   * @param scenario - Type of authentication scenario to test
   */
  async handleAuth0Scenario(credentials: UserCredentials, scenario: 'success' | 'invalid_credentials' | 'network_error'): Promise<void> {
    await this.clickLoginButton();
    await this.waitForAuth0Redirect();

    switch (scenario) {
      case 'success':
        await this.fillAuth0Credentials(credentials);
        await this.waitForLoginSuccess();
        break;
        
      case 'invalid_credentials':
        await this.fillAuth0Credentials({ 
          email: 'invalid@example.com', 
          password: 'wrongpassword' 
        });
        await this.waitForAuth0Error();
        break;
        
      case 'network_error':
        // This would typically be handled by network mocking in tests
        await this.fillAuth0Credentials(credentials);
        break;
    }
  }
}