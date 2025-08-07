# Authentication Tests

This directory contains comprehensive end-to-end tests for the authentication functionality of the stock analysis application.

## Test Coverage

### Requirements Covered
- **Requirement 1.1**: Login interface with Auth0 integration
- **Requirement 1.2**: Successful authentication and redirect to dashboard
- **Requirement 1.3**: Logout functionality with session clearing
- **Requirement 1.4**: Protected route access control for unauthenticated users

### Test Files

#### `authentication.spec.ts`
Core authentication flow tests covering:
- Login page display and Auth0 integration
- Successful authentication workflow
- Logout functionality and session management
- Error handling for authentication failures
- Session persistence across page refreshes
- Concurrent authentication attempts

#### `protected-routes.spec.ts`
Protected route access tests covering:
- Redirect behavior for unauthenticated users
- Access control for all protected endpoints
- Deep-linking to protected routes
- API endpoint protection
- Session timeout handling
- Query parameter preservation during redirects

#### `auth-integration.spec.ts`
Comprehensive integration tests covering:
- Complete authentication workflows
- Cross-browser compatibility
- Multi-tab session management
- Authentication state persistence
- Error recovery scenarios

### Page Objects

#### `LoginPage.ts`
Page Object Model for authentication interactions:
- Login page element selectors
- Auth0 integration methods
- Authentication flow helpers
- Session state verification
- Error handling utilities

### Test Fixtures

#### `auth-fixtures.ts`
Reusable test fixtures providing:
- Pre-configured page objects
- Test credential management
- Authentication state setup
- Mock response configuration
- Helper functions for common operations

## Running Authentication Tests

### Prerequisites
1. **Start the Flask application first:**
   ```bash
   python src/akinator_assets.py
   ```
   The application should be running on `http://localhost:8080`

2. **Set up test environment variables:**
   ```bash
   export TEST_USER_EMAIL="your-test-user@example.com"
   export TEST_USER_PASSWORD="your-test-password"
   ```

3. **Install test dependencies:**
   ```bash
   npm install
   npx playwright install
   ```

### Easy Way - Using npm Scripts
```bash
# MINIMAL - Run only essential tests (7 tests, ~10 seconds) ⭐ RECOMMENDED
npm run test:auth:minimal

# MINIMAL - Run essential tests in headed mode
npm run test:auth:minimal:headed

# FAST - Run only Chrome tests (42 tests, ~2 minutes)
npm run test:auth:fast

# FAST - Run only Chrome tests in headed mode
npm run test:auth:fast:headed

# FULL - Run all authentication tests (Chrome, Firefox, Mobile - ~10+ minutes)
npm run test:auth

# Run in debug mode
npm run test:auth:debug
```

### Manual Way - Direct Playwright Commands
```bash
# Run all auth tests
npx playwright test tests/e2e/auth/ --config=tests/e2e/auth/auth.config.ts

# Run specific test files
npx playwright test tests/e2e/auth/authentication.spec.ts --config=tests/e2e/auth/auth.config.ts
npx playwright test tests/e2e/auth/protected-routes.spec.ts --config=tests/e2e/auth/auth.config.ts
npx playwright test tests/e2e/auth/auth-integration.spec.ts --config=tests/e2e/auth/auth.config.ts

# Run in headed mode
npx playwright test tests/e2e/auth/ --config=tests/e2e/auth/auth.config.ts --headed

# Run specific browser
npx playwright test tests/e2e/auth/ --config=tests/e2e/auth/auth.config.ts --project=auth-chrome
```

### Running All Authentication Tests
```bash
npx playwright test tests/e2e/auth/
```

### Running Specific Test Files
```bash
# Authentication flow tests
npx playwright test tests/e2e/auth/authentication.spec.ts

# Protected route tests
npx playwright test tests/e2e/auth/protected-routes.spec.ts

# Integration tests
npx playwright test tests/e2e/auth/auth-integration.spec.ts
```

### Running with Specific Configuration
```bash
npx playwright test --config=tests/e2e/auth/auth.config.ts
```

### Running in Different Browsers
```bash
# Chrome
npx playwright test --project=auth-chrome

# Firefox
npx playwright test --project=auth-firefox

# Mobile
npx playwright test --project=auth-mobile
```

## Test Data Management

### Environment Variables
- `TEST_USER_EMAIL`: Email for test user account
- `TEST_USER_PASSWORD`: Password for test user account
- `BASE_URL`: Application base URL (default: http://localhost:8080)

### Test Credentials
Test credentials are managed through the `TestDataManager` class:
- Valid credentials for successful authentication
- Invalid credentials for error testing
- Multiple user scenarios for concurrent testing

### Mock Data
Authentication tests use mocked Auth0 responses for:
- Successful authentication flows
- Error scenarios (invalid credentials, network failures)
- Timeout situations

## Test Artifacts

### Screenshots
- Captured on test failures
- Stored in `test-results/auth-artifacts/`
- Include full page screenshots for debugging

### Videos
- Recorded for failed tests
- Show complete user interaction flow
- Useful for debugging authentication issues

### Traces
- Detailed execution traces for failed tests
- Include network requests, DOM changes, and user actions
- Can be viewed in Playwright trace viewer

## Performance Tips

### For Daily Development (Recommended)
Use the minimal configuration with only essential tests:
```bash
npm run test:auth:minimal
```

### For Thorough Testing
Use the fast configuration which runs more comprehensive tests:
```bash
npm run test:auth:fast
```

### For Full Cross-Browser Testing
Use the full configuration which runs across multiple browsers:
```bash
npm run test:auth
```

### Running Specific Tests
```bash
# Run a specific test file (fast)
npx playwright test --config=tests/e2e/auth/auth-fast.config.ts tests/e2e/auth/authentication.spec.ts

# Run tests matching a pattern (fast)
npx playwright test --config=tests/e2e/auth/auth-fast.config.ts -g "login"
```

### Speed Comparison
- **Minimal config**: ~10 seconds total (7 essential tests) ⭐
- **Fast config**: ~2 minutes total (42 comprehensive tests)
- **Full config**: ~10+ minutes total (126 tests across 3 browsers)

## Debugging Authentication Tests

### Common Issues
1. **Auth0 Redirect Timeouts**: Increase timeout values in test configuration
2. **Session State Issues**: Ensure proper session cleanup between tests
3. **Network Errors**: Check application availability and Auth0 configuration
4. **Element Not Found**: Verify selectors match current UI implementation

### Debug Mode
Run tests in headed mode to see browser interactions:
```bash
npx playwright test tests/e2e/auth/ --headed --debug
```

### Trace Viewer
View detailed test execution traces:
```bash
npx playwright show-trace test-results/auth-artifacts/trace.zip
```

## Maintenance

### Updating Selectors
When UI changes occur, update selectors in:
- `LoginPage.ts` - Main page object selectors
- Test files - Any test-specific selectors

### Adding New Authentication Scenarios
1. Add test data to `TestDataManager`
2. Create new test cases in appropriate spec files
3. Update fixtures if new setup is required
4. Document new requirements coverage

### Performance Considerations
- Authentication tests may be slower due to Auth0 redirects
- Use appropriate timeouts for network operations
- Consider mocking Auth0 responses for faster test execution
- Run tests in parallel where possible

## CI/CD Integration

### GitHub Actions
Authentication tests are configured to run in CI with:
- Multiple browser support
- Retry logic for flaky tests
- Artifact collection for failures
- Test result reporting

### Environment Setup
CI environments should include:
- Test user credentials as secrets
- Application deployment
- Auth0 test configuration
- Proper network access for Auth0 redirects