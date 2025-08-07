import { defineConfig } from '@playwright/test';

/**
 * Fast authentication test configuration for development
 * Runs only Chrome with minimal overhead
 */
export default defineConfig({
  // Test directory for authentication tests (current directory since config is in auth folder)
  testDir: '.',
  
  // Shorter timeout for faster feedback
  timeout: 30000,
  
  // Expect timeout for assertions
  expect: {
    timeout: 5000
  },
  
  // No retries for faster feedback
  retries: 0,
  
  // Single worker for predictable execution
  workers: 1,
  
  // Minimal reporting
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/auth-report', open: 'never' }]
  ],
  
  // Single Chrome project only
  projects: [
    {
      name: 'chrome-fast',
      use: {
        browserName: 'chromium',
        viewport: { width: 1280, height: 720 },
        ignoreHTTPSErrors: true,
        video: 'off',
        screenshot: 'only-on-failure',
        trace: 'off'
      }
    }
  ],
  
  // Base URL for tests
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8080',
    ignoreHTTPSErrors: true,
    screenshot: 'only-on-failure',
    video: 'off',
    trace: 'off'
  },
  
  // Output directory for test artifacts
  outputDir: 'test-results/auth-artifacts',
  
  // Test metadata
  metadata: {
    testType: 'authentication-fast',
    description: 'Fast authentication tests for development'
  }
});