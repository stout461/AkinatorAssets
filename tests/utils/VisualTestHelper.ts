import { Page, expect, Locator } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Interface for visual comparison options
 */
export interface VisualComparisonOptions {
  threshold?: number;
  maxDiffPixels?: number;
  animations?: 'disabled' | 'allow';
  clip?: { x: number; y: number; width: number; height: number };
  fullPage?: boolean;
  mask?: Locator[];
}

/**
 * Interface for screenshot stabilization options
 */
export interface StabilizationOptions {
  waitForAnimations?: boolean;
  waitForFonts?: boolean;
  waitForImages?: boolean;
  customWaitCondition?: () => Promise<void>;
}

/**
 * Helper class for visual regression testing and screenshot comparison utilities
 * Provides methods for consistent visual testing across different browsers and environments
 */
export class VisualTestHelper {
  private static readonly SCREENSHOTS_DIR = 'tests/screenshots';
  private static readonly BASELINE_DIR = 'tests/screenshots/baseline';
  private static readonly DIFF_DIR = 'tests/screenshots/diff';

  /**
   * Initialize screenshot directories if they don't exist
   */
  static initializeDirectories(): void {
    const dirs = [
      this.SCREENSHOTS_DIR,
      this.BASELINE_DIR,
      this.DIFF_DIR
    ];

    dirs.forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  /**
   * Compare a chart screenshot with baseline and handle visual regression testing
   * @param page - Playwright page instance
   * @param testName - Name identifier for the test/screenshot
   * @param options - Visual comparison options
   */
  static async compareChartScreenshot(
    page: Page, 
    testName: string, 
    options: VisualComparisonOptions = {}
  ): Promise<void> {
    this.initializeDirectories();

    // Wait for chart to stabilize before taking screenshot
    await this.waitForChartStabilization(page);

    // Mask dynamic elements if specified
    if (options.mask) {
      await this.maskDynamicElements(page, options.mask);
    }

    // Default options for chart screenshots
    const defaultOptions: VisualComparisonOptions = {
      threshold: 0.2,
      maxDiffPixels: 100,
      animations: 'disabled',
      fullPage: false,
      ...options
    };

    // Take screenshot and compare with baseline
    const screenshotName = `${testName}-chart`;
    
    try {
      await expect(page).toHaveScreenshot(`${screenshotName}.png`, {
        threshold: defaultOptions.threshold,
        maxDiffPixels: defaultOptions.maxDiffPixels,
        animations: defaultOptions.animations,
        clip: defaultOptions.clip,
        fullPage: defaultOptions.fullPage,
        mask: defaultOptions.mask
      });
    } catch (error) {
      // Save the current screenshot for debugging
      await page.screenshot({
        path: path.join(this.DIFF_DIR, `${screenshotName}-current.png`),
        fullPage: defaultOptions.fullPage,
        clip: defaultOptions.clip
      });
      throw error;
    }
  }

  /**
   * Wait for chart to stabilize before taking screenshots
   * Ensures consistent visual testing by waiting for all chart elements to render
   * @param page - Playwright page instance
   * @param options - Stabilization options
   */
  static async waitForChartStabilization(
    page: Page, 
    options: StabilizationOptions = {}
  ): Promise<void> {
    const {
      waitForAnimations = true,
      waitForFonts = true,
      waitForImages = true,
      customWaitCondition
    } = options;

    // Wait for network requests to complete
    await page.waitForLoadState('networkidle');

    // Wait for chart container to be visible
    const chartSelectors = [
      '#chart-container',
      '.chart-canvas',
      '[data-testid="chart"]',
      '.plotly-graph-div'
    ];

    for (const selector of chartSelectors) {
      try {
        await page.waitForSelector(selector, { state: 'visible', timeout: 5000 });
        break;
      } catch {
        // Continue to next selector
      }
    }

    // Wait for animations to complete if enabled
    if (waitForAnimations) {
      await this.waitForAnimationsToComplete(page);
    }

    // Wait for fonts to load if enabled
    if (waitForFonts) {
      await this.waitForFontsToLoad(page);
    }

    // Wait for images to load if enabled
    if (waitForImages) {
      await this.waitForImagesToLoad(page);
    }

    // Execute custom wait condition if provided
    if (customWaitCondition) {
      await customWaitCondition();
    }

    // Additional wait for chart rendering to complete
    await page.waitForTimeout(1000);
  }

  /**
   * Mask dynamic elements that change between test runs
   * @param page - Playwright page instance
   * @param additionalMasks - Additional locators to mask
   */
  static async maskDynamicElements(page: Page, additionalMasks: Locator[] = []): Promise<void> {
    // Common dynamic elements to mask
    const dynamicSelectors = [
      '.timestamp',
      '.current-time',
      '.last-updated',
      '[data-testid="timestamp"]',
      '.real-time-price',
      '.live-data'
    ];

    const masks: Locator[] = [...additionalMasks];

    // Add common dynamic elements to mask list
    for (const selector of dynamicSelectors) {
      try {
        const elements = page.locator(selector);
        const count = await elements.count();
        if (count > 0) {
          masks.push(elements);
        }
      } catch {
        // Ignore if selector doesn't exist
      }
    }

    // Apply CSS to hide masked elements
    if (masks.length > 0) {
      await page.addStyleTag({
        content: `
          .visual-test-mask {
            background-color: #cccccc !important;
            color: transparent !important;
          }
        `
      });

      // Add mask class to elements
      for (const mask of masks) {
        try {
          await mask.evaluateAll(elements => {
            elements.forEach(el => el.classList.add('visual-test-mask'));
          });
        } catch {
          // Ignore if element is not found
        }
      }
    }
  }

  /**
   * Wait for CSS animations to complete
   * @param page - Playwright page instance
   */
  private static async waitForAnimationsToComplete(page: Page): Promise<void> {
    await page.waitForFunction(() => {
      const animations = document.getAnimations();
      return animations.every(animation => 
        animation.playState === 'finished' || animation.playState === 'idle'
      );
    }, undefined, { timeout: 5000 }).catch(() => {
      // Ignore timeout - animations might not be present
    });
  }

  /**
   * Wait for web fonts to load
   * @param page - Playwright page instance
   */
  private static async waitForFontsToLoad(page: Page): Promise<void> {
    await page.waitForFunction(() => {
      return document.fonts.ready;
    }, undefined, { timeout: 5000 }).catch(() => {
      // Ignore timeout - fonts might already be loaded
    });
  }

  /**
   * Wait for images to load
   * @param page - Playwright page instance
   */
  private static async waitForImagesToLoad(page: Page): Promise<void> {
    await page.waitForFunction(() => {
      const images = Array.from(document.images);
      return images.every(img => img.complete);
    }, undefined, { timeout: 5000 }).catch(() => {
      // Ignore timeout - images might not be present
    });
  }

  /**
   * Take a full page screenshot with stabilization
   * @param page - Playwright page instance
   * @param name - Screenshot name
   * @param options - Screenshot options
   */
  static async takeStabilizedScreenshot(
    page: Page, 
    name: string, 
    options: VisualComparisonOptions = {}
  ): Promise<void> {
    this.initializeDirectories();
    
    await this.waitForChartStabilization(page);
    
    if (options.mask) {
      await this.maskDynamicElements(page, options.mask);
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}-${timestamp}.png`;
    
    await page.screenshot({
      path: path.join(this.SCREENSHOTS_DIR, filename),
      fullPage: options.fullPage ?? true,
      clip: options.clip,
      animations: options.animations ?? 'disabled'
    });
  }

  /**
   * Compare element screenshot with baseline
   * @param element - Playwright locator for the element
   * @param testName - Name identifier for the test
   * @param options - Visual comparison options
   */
  static async compareElementScreenshot(
    element: Locator, 
    testName: string, 
    options: VisualComparisonOptions = {}
  ): Promise<void> {
    this.initializeDirectories();

    const defaultOptions = {
      threshold: 0.2,
      maxDiffPixels: 50,
      animations: 'disabled' as const,
      ...options
    };

    await expect(element).toHaveScreenshot(`${testName}-element.png`, {
      threshold: defaultOptions.threshold,
      maxDiffPixels: defaultOptions.maxDiffPixels,
      animations: defaultOptions.animations
    });
  }

  /**
   * Validate dark mode styling by comparing screenshots
   * @param page - Playwright page instance
   * @param testName - Name identifier for the test
   */
  static async validateDarkModeScreenshot(page: Page, testName: string): Promise<void> {
    // Take screenshot in light mode
    await this.compareChartScreenshot(page, `${testName}-light-mode`);

    // Switch to dark mode (assuming there's a toggle)
    const darkModeSelectors = [
      '[data-testid="dark-mode-toggle"]',
      '.dark-mode-toggle',
      '#dark-mode-switch'
    ];

    for (const selector of darkModeSelectors) {
      try {
        const toggle = page.locator(selector);
        if (await toggle.isVisible()) {
          await toggle.click();
          break;
        }
      } catch {
        // Continue to next selector
      }
    }

    // Wait for theme change to apply
    await page.waitForTimeout(500);
    await this.waitForChartStabilization(page);

    // Take screenshot in dark mode
    await this.compareChartScreenshot(page, `${testName}-dark-mode`);
  }

  /**
   * Test responsive layout by taking screenshots at different viewport sizes
   * @param page - Playwright page instance
   * @param testName - Name identifier for the test
   * @param viewports - Array of viewport sizes to test
   */
  static async testResponsiveScreenshots(
    page: Page, 
    testName: string, 
    viewports: Array<{name: string, width: number, height: number}> = []
  ): Promise<void> {
    const defaultViewports = [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1920, height: 1080 }
    ];

    const testViewports = viewports.length > 0 ? viewports : defaultViewports;

    for (const viewport of testViewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await this.waitForChartStabilization(page);
      await this.compareChartScreenshot(page, `${testName}-${viewport.name}`);
    }
  }

  /**
   * Clean up old screenshot files
   * @param daysOld - Number of days old files to delete (default: 7)
   */
  static cleanupOldScreenshots(daysOld: number = 7): void {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);

    const dirs = [this.SCREENSHOTS_DIR, this.DIFF_DIR];

    dirs.forEach(dir => {
      if (fs.existsSync(dir)) {
        const files = fs.readdirSync(dir);
        files.forEach(file => {
          const filePath = path.join(dir, file);
          const stats = fs.statSync(filePath);
          if (stats.mtime < cutoffDate) {
            fs.unlinkSync(filePath);
          }
        });
      }
    });
  }
}