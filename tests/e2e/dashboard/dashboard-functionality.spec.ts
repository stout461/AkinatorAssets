import { test, expect } from '../../fixtures/fast-auth-fixtures';
import { DashboardPage } from '../../pages/DashboardPage';
import { TestDataManager } from '../../utils/TestDataManager';

test.describe('Dashboard Core Functionality', () => {
    let dashboardPage: DashboardPage;

    test.beforeEach(async ({ authenticatedPage }) => {
        // Use pre-authenticated page - no login needed!
        dashboardPage = new DashboardPage(authenticatedPage);
        await dashboardPage.navigateTo();
    });

    test('should load and display stock chart for valid ticker', async () => {
        // Requirement 2.1: WHEN a user enters a valid stock ticker THEN the system SHALL load and display the stock chart with price data
        const ticker = TestDataManager.getValidTickers()[0]; // AAPL
        
        await dashboardPage.enterTicker(ticker);
        await dashboardPage.clickSubmit();
        await dashboardPage.waitForChartLoad();
        
        // Verify chart is loaded and visible
        await dashboardPage.verifyChartLoaded();
        expect(await dashboardPage.isChartVisible()).toBe(true);
        expect(await dashboardPage.getTickerValue()).toBe(ticker);
    });

    test('should update chart when different time period is selected', async () => {
        // Requirement 2.2: WHEN a user selects different time periods THEN the system SHALL update the chart data accordingly
        const ticker = TestDataManager.getValidTickers()[0]; // AAPL
        
        // Load initial chart with 1Y period
        await dashboardPage.loadStockData(ticker, '1Y');
        await dashboardPage.verifyChartLoaded();
        
        // Change to 1M period and verify update
        await dashboardPage.selectPeriod('1M');
        await dashboardPage.clickSubmit();
        await dashboardPage.waitForChartLoad();
        
        // Verify period selection and chart update
        expect(await dashboardPage.getSelectedPeriod()).toBe('1M');
        await dashboardPage.verifyChartLoaded();
    });
});