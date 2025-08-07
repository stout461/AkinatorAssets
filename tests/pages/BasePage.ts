import { Page, Locator, expect } from '@playwright/test';

/**
 * Abstract base class for all page objects providing common navigation and utility methods
 * Implements shared functionality across all pages in the application
 */
export abstract class BasePage {
  protected page: Page;
  protected baseURL: string;

  constructor(page: Page) {
    this.page = page;
    this.baseURL = process.env.BASE_URL || 'http://localhost:8080';
  }

  /**
   * Abstract method that must be implemented by each page to define page-specific loading logic
   */
  abstract waitForPageLoad(): Promise<void>;

  /**
   * Navigate to a specific path relative to the base URL
   * @param path - The path to navigate to (e.g., '/dashboard', '/login')
   */
  async navigateTo(path: string): Promise<void> {
    const url = `${this.baseURL}${path}`;
    await this.page.goto(url);
    await this.waitForPageLoad();
  }

  /**
   * Wait for any loading indicators to disappear
   * Common loading states across the application
   */
  async waitForLoadingToComplete(): Promise<void> {
    // Wait for common loading indicators to disappear
    const loadingSelectors = [
      '.loading-spinner',
      '.loading-indicator',
      '[data-testid="loading"]',
      '.spinner'
    ];

    for (const selector of loadingSelectors) {
      try {
        await this.page.waitForSelector(selector, { state: 'hidden', timeout: 5000 });
      } catch {
        // Ignore if selector doesn't exist
      }
    }

    // Wait for network idle to ensure all requests are complete
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Take a screenshot with a specific name for debugging or visual testing
   * @param name - Name for the screenshot file
   */
  async takeScreenshot(name: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}-${timestamp}.png`;
    await this.page.screenshot({ 
      path: `tests/screenshots/${filename}`,
      fullPage: true 
    });
  }

  /**
   * Wait for a specific element to be visible on the page
   * @param selector - CSS selector or locator for the element
   * @param timeout - Optional timeout in milliseconds (default: 10000)
   */
  async waitForElement(selector: string | Locator, timeout: number = 10000): Promise<Locator> {
    const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
    await locator.waitFor({ state: 'visible', timeout });
    return locator;
  }

  /**
   * Click an element and wait for navigation if it occurs
   * @param selector - CSS selector or locator for the element to click
   */
  async clickAndWaitForNavigation(selector: string | Locator): Promise<void> {
    const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
    
    await Promise.all([
      this.page.waitForLoadState('networkidle'),
      locator.click()
    ]);
  }

  /**
   * Fill an input field and trigger change events
   * @param selector - CSS selector or locator for the input field
   * @param value - Value to fill in the input
   */
  async fillInput(selector: string | Locator, value: string): Promise<void> {
    const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
    await locator.fill(value);
    await locator.press('Tab'); // Trigger blur event
  }

  /**
   * Wait for an element to contain specific text
   * @param selector - CSS selector or locator for the element
   * @param text - Text to wait for
   * @param timeout - Optional timeout in milliseconds (default: 10000)
   */
  async waitForText(selector: string | Locator, text: string, timeout: number = 10000): Promise<void> {
    const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
    await expect(locator).toContainText(text, { timeout });
  }

  /**
   * Check if an element is visible on the page
   * @param selector - CSS selector or locator for the element
   * @returns Promise<boolean> - True if element is visible, false otherwise
   */
  async isElementVisible(selector: string | Locator): Promise<boolean> {
    try {
      const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
      await locator.waitFor({ state: 'visible', timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get the current page URL
   * @returns Promise<string> - Current page URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  /**
   * Wait for the page title to match a specific value
   * @param title - Expected page title
   * @param timeout - Optional timeout in milliseconds (default: 10000)
   */
  async waitForTitle(title: string, timeout: number = 10000): Promise<void> {
    await this.page.waitForFunction(
      (expectedTitle) => document.title === expectedTitle,
      title,
      { timeout }
    );
  }

  /**
   * Scroll an element into view
   * @param selector - CSS selector or locator for the element
   */
  async scrollIntoView(selector: string | Locator): Promise<void> {
    const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
    await locator.scrollIntoViewIfNeeded();
  }

  /**
   * Get the text content of an element
   * @param selector - CSS selector or locator for the element
   * @returns Promise<string> - Text content of the element
   */
  async getElementText(selector: string | Locator): Promise<string> {
    const locator = typeof selector === 'string' ? this.page.locator(selector) : selector;
    return await locator.textContent() || '';
  }

  /**
   * Wait for an error message to appear and return its text
   * @param timeout - Optional timeout in milliseconds (default: 5000)
   * @returns Promise<string> - Error message text
   */
  async waitForErrorMessage(timeout: number = 5000): Promise<string> {
    const errorSelectors = [
      '.error-message',
      '.alert-danger',
      '[data-testid="error"]',
      '.error'
    ];

    for (const selector of errorSelectors) {
      try {
        const element = await this.page.waitForSelector(selector, { timeout });
        const text = await element.textContent();
        if (text) return text.trim();
      } catch {
        // Continue to next selector
      }
    }

    throw new Error('No error message found within timeout');
  }
}