import { defineConfig } from '@playwright/test';

/**
 * Minimal authentication test configuration
 * Runs only essential tests with maximum speed
 */
export default defineConfig({
  testDir: '.',
  
  // Include only the simple test file
  testMatch: '**/auth-simple.spec.ts',
  
  // Fast timeouts
  timeout: 15000,
  expect: { timeout: 3000 },
  
  // No retries - fail fast
  retries: 0,
  workers: 1,
  
  // Minimal reporting
  reporter: [['list']],
  
  // Single Chrome project
  projects: [{
    name: 'chrome-minimal',
    use: {
      browserName: 'chromium',
      viewport: { width: 1280, height: 720 },
      ignoreHTTPSErrors: true,
      video: 'off',
      screenshot: 'only-on-failure',
      trace: 'off'
    }
  }],
  
  use: {
    baseURL: 'http://localhost:8080',
    ignoreHTTPSErrors: true,
    screenshot: 'only-on-failure',
    video: 'off',
    trace: 'off'
  },
  
  outputDir: 'test-results/auth-minimal'
});