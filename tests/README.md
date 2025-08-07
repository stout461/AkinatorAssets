# UI Test Automation

Minimal, focused end-to-end tests for the stock analysis web application using Playwright.

## Quick Start

```bash
# Run complete test suite
npm run test:all

# Run with visible browser
npm run test:all:headed

# Run quick essential tests only
npm run test:quick
```

## Test Structure (Minimal)

### 🔐 Authentication (`tests/e2e/auth/`)
- `auth-simple.spec.ts` - Basic login/logout and route protection

### 📊 Dashboard (`tests/e2e/dashboard/`)
- `dashboard-functionality.spec.ts` - Core ticker entry and chart loading

### 📈 Chart Interactions (`tests/e2e/chart/`)
- `technical-indicators.spec.ts` - RSI, MACD, Volume, Candlestick toggles
- `chart-modes.spec.ts` - Fibonacci, Elliott Wave, Trendline modes
- `moving-averages.spec.ts` - Standard and custom moving averages
- `multiple-modes.spec.ts` - Combined indicator functionality

## Key Features

✅ **Fast Authentication** - Global login setup, no repeated Auth0 calls  
✅ **Chrome Only** - Optimized for speed and development  
✅ **Minimal Coverage** - Essential functionality only  
✅ **Page Object Model** - Maintainable test structure  

## Commands

```bash
# Complete test suite with setup
npm run test:all

# Headed mode (visible browser)
npm run test:all:headed

# Debug mode with inspector
npm run test:all:debug

# Quick smoke test
npm run test:quick

# Individual test categories
npx playwright test tests/e2e/auth/
npx playwright test tests/e2e/dashboard/
npx playwright test tests/e2e/chart/
```

## Configuration

- **Browser**: Chrome only (configured in `playwright.config.ts`)
- **Authentication**: Global setup with session reuse
- **Artifacts**: Screenshots and videos on failure in `test-results/`
- **Reports**: HTML report generated automatically

## Development Notes

- Tests use `fast-auth-fixtures.ts` to avoid repeated logins
- Chart tests focus on toggle behavior and mode switching
- Minimal test cases - success scenarios only
- ~30 second execution time for full suite