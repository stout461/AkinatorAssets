import { chromium, FullConfig } from '@playwright/test';
import { TestDataManager } from './utils/TestDataManager';
import { LoginPage } from './pages/LoginPage';

/**
 * Global authentication setup
 * Performs login once and saves authentication state for reuse across tests
 */
async function globalSetup(config: FullConfig) {
  console.log('🔐 Setting up global authentication...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    const baseURL = process.env.BASE_URL || 'http://localhost:8080';
    const testCredentials = TestDataManager.getTestCredentials();
    
    console.log(`🌐 Authenticating user: ${testCredentials.email}`);
    
    // Perform login
    const loginPage = new LoginPage(page);
    await loginPage.navigateToLogin();
    await loginPage.login(testCredentials);
    await loginPage.verifyLoginSuccess();
    
    console.log('✅ Authentication successful');
    
    // Save authentication state
    await context.storageState({ path: 'tests/auth-state.json' });
    console.log('💾 Authentication state saved to tests/auth-state.json');
    
  } catch (error) {
    console.error('❌ Global authentication setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
  
  console.log('✅ Global authentication setup complete');
}

export default globalSetup;