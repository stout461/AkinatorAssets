# Dashboard Functionality Tests

This directory contains UI tests for the core dashboard functionality of the stock analysis application.

## Test Coverage

### DashboardPage Class (`../../pages/DashboardPage.ts`)
- **Essential Selectors**: Ticker input, submit button, period buttons, chart container, loading indicators
- **Core Methods**: 
  - `enterTicker()` - Enter stock ticker symbol
  - `selectPeriod()` - Select time period (1M, 3M, 6M, 1Y, 5Y)
  - `clickSubmit()` - Submit form to load data
  - `waitForChartLoad()` - Wait for chart loading to complete
  - `verifyChartLoaded()` - Verify chart has loaded successfully
  - `loadStockData()` - Helper method for complete ticker entry and chart loading

### Test Files

#### `dashboard-functionality.spec.ts`
- **Test 1**: Load and display stock chart for valid ticker (Requirement 2.1)
- **Test 2**: Update chart when different time period is selected (Requirement 2.2)

#### `ticker-entry.spec.ts`
- **Test 1**: Display loading indicator during chart data fetch (Requirement 2.3)
- **Test 2**: Enable detailed view navigation after chart loads (Requirement 2.5)

#### `period-selection.spec.ts`
- **Test 1-5**: Load chart data for each time period (1M, 3M, 6M, 1Y, 5Y) (Requirement 2.2)
- **Test 6**: Maintain ticker value when switching periods

## Requirements Coverage

✅ **Requirement 2.1**: Valid stock ticker loading and chart display  
✅ **Requirement 2.2**: Time period selection and chart updates  
✅ **Requirement 2.3**: Loading indicator display during data fetch  
✅ **Requirement 2.5**: Detailed view navigation enablement  

## Test Philosophy

Following the **Minimal & Focused Approach**:
- **7 total tests** focusing on success scenarios only
- **Fast execution** (~10-30 seconds per test suite)
- **Essential functionality** coverage without complex error handling
- **Practical value** over comprehensive coverage

## Running the Tests

### Prerequisites
- Application running on `http://localhost:8080`
- Playwright installed and configured
- **Authentication Setup**: The application requires Auth0 authentication to access the dashboard

### Authentication Requirement
The dashboard tests require valid authentication credentials to access the main application. The tests use the existing `auth-fixtures` to handle login flow.

### Commands
```bash
# Run page object demo (shows implementation without auth)
npm test tests/e2e/dashboard/dashboard-demo.spec.ts

# Run full dashboard tests (requires working Auth0 setup)
npm test tests/e2e/dashboard/

# Run specific test file
npm test tests/e2e/dashboard/dashboard-functionality.spec.ts

# Run with custom script (Chromium only)
node run-dashboard-tests.js
```

### Authentication Setup
To run the full dashboard tests, ensure:
1. Auth0 is properly configured in `.env` file
2. Test credentials are available in the auth fixtures
3. Auth0 domain is accessible and configured for testing

### Test Data
Tests use `TestDataManager.getValidTickers()` which provides:
- AAPL (Apple Inc.)
- GOOGL (Alphabet Inc.)
- MSFT (Microsoft Corporation)
- TSLA (Tesla Inc.)

## Implementation Notes

- Tests focus on **success scenarios only** as specified in the task
- **Minimal test count** (1-2 tests per core functionality)
- **Essential selectors** based on actual HTML structure
- **Fast execution** with practical timeouts
- **No complex error handling** or edge case testing (covered in other tasks)