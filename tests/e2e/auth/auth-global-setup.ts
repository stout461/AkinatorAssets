import { chromium, FullConfig } from '@playwright/test';
import { TestDataManager } from '../../utils/TestDataManager';

/**
 * Global setup for authentication tests
 * Prepares test environment and validates prerequisites
 */
async function globalSetup(config: FullConfig) {
  console.log('🔧 Setting up authentication test environment...');
  
  // Validate environment variables
  const requiredEnvVars = [
    'TEST_USER_EMAIL',
    'TEST_USER_PASSWORD'
  ];
  
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    console.warn(`⚠️  Missing environment variables: ${missingVars.join(', ')}`);
    console.warn('Using default test credentials. Set these variables for production testing.');
  }
  
  // Validate test data
  try {
    const testCredentials = TestDataManager.getTestCredentials();
    console.log(`✅ Test credentials configured for: ${testCredentials.email}`);
  } catch (error) {
    console.error('❌ Failed to load test credentials:', error);
    throw error;
  }
  
  // Validate application is accessible
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    const baseURL = process.env.BASE_URL || 'http://localhost:8080';
    console.log(`🌐 Checking application accessibility at: ${baseURL}`);
    
    const response = await page.goto(`${baseURL}/login`, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    if (!response || response.status() !== 200) {
      console.warn(`⚠️  Application may not be running. Status: ${response?.status()}`);
      console.warn('Please ensure the Flask application is running: python src/akinator_assets.py');
      // Don't throw error, just warn
    } else {
      // Verify login page loads correctly
      const loginButton = page.locator('.login-button');
      await loginButton.waitFor({ timeout: 10000 });
      console.log('✅ Application is accessible and login page loads correctly');
    }
    
  } catch (error) {
    console.warn('⚠️  Application accessibility check failed:', error);
    console.warn('Please ensure the Flask application is running: python src/akinator_assets.py');
    // Don't throw error, just warn
  } finally {
    await context.close();
    await browser.close();
  }
  
  // Create test artifacts directory
  const fs = require('fs');
  const path = require('path');
  
  const artifactsDir = path.join(process.cwd(), 'test-results', 'auth-artifacts');
  if (!fs.existsSync(artifactsDir)) {
    fs.mkdirSync(artifactsDir, { recursive: true });
    console.log(`📁 Created test artifacts directory: ${artifactsDir}`);
  }
  
  // Log test configuration
  console.log('🔧 Authentication test configuration:');
  console.log(`   - Base URL: ${process.env.BASE_URL || 'http://localhost:8080'}`);
  console.log(`   - Workers: ${config.workers}`);
  console.log(`   - Projects: ${config.projects?.map(p => p.name).join(', ')}`);
  
  console.log('✅ Authentication test environment setup complete');
}

export default globalSetup;