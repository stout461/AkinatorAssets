import { defineConfig } from '@playwright/test';

/**
 * Authentication-specific test configuration
 * Extends the main Playwright config with auth-specific settings
 */
export default defineConfig({
  // Test directory for authentication tests (current directory since config is in auth folder)
  testDir: '.',
  
  // Test timeout for authentication flows (longer due to Auth0 redirects)
  timeout: 60000,
  
  // Expect timeout for assertions
  expect: {
    timeout: 10000
  },
  
  // Retry failed tests (auth flows can be flaky)
  retries: process.env.CI ? 2 : 0,
  
  // Run tests in parallel
  workers: process.env.CI ? 2 : 2,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'test-results/auth-report' }],
    ['json', { outputFile: 'test-results/auth-results.json' }],
    ['junit', { outputFile: 'test-results/auth-junit.xml' }]
  ],
  
  // No global setup - assumes server is already running
  
  // Use projects for different authentication scenarios
  projects: [
    {
      name: 'auth-chrome',
      use: {
        browserName: 'chromium',
        channel: 'chrome',
        viewport: { width: 1280, height: 720 },
        ignoreHTTPSErrors: true,
        video: 'off', // Disable video for faster tests
        screenshot: 'only-on-failure',
        trace: 'off' // Disable trace for faster tests
      }
    },
    // Uncomment these for cross-browser testing
    // {
    //   name: 'auth-firefox',
    //   use: {
    //     browserName: 'firefox',
    //     viewport: { width: 1280, height: 720 },
    //     ignoreHTTPSErrors: true,
    //     video: 'retain-on-failure',
    //     screenshot: 'only-on-failure'
    //   }
    // },
    // {
    //   name: 'auth-mobile',
    //   use: {
    //     browserName: 'chromium',
    //     ...require('@playwright/test').devices['iPhone 12'],
    //     ignoreHTTPSErrors: true,
    //     video: 'retain-on-failure',
    //     screenshot: 'only-on-failure'
    //   }
    // }
  ],
  
  // Note: Web server should be started manually before running tests
  // Run: python src/akinator_assets.py
  
  // Base URL for tests
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8080',
    
    // Browser context options
    ignoreHTTPSErrors: true,
    
    // Capture screenshots and videos on failure
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Authentication-specific settings
    extraHTTPHeaders: {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
  },
  
  // Output directory for test artifacts
  outputDir: 'test-results/auth-artifacts',
  
  // Test metadata
  metadata: {
    testType: 'authentication',
    requirements: ['1.1', '1.2', '1.3', '1.4'],
    description: 'Authentication flow and protected route access tests'
  }
});