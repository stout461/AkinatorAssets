import { test, expect } from '../../fixtures/fast-auth-fixtures';
import { ChartPage } from '../../pages/ChartPage';
import { TestDataManager } from '../../utils/TestDataManager';

test.describe('Chart Mode Switching', () => {
    let chartPage: ChartPage;
    const ticker = TestDataManager.getValidTickers()[0]; // AAPL

    test.beforeEach(async ({ authenticatedPage }) => {
        // Use pre-authenticated page - no login needed!
        chartPage = new ChartPage(authenticatedPage);
        await chartPage.navigateToDetailedChart(ticker);
        await chartPage.waitForPageLoad();
        await chartPage.waitForChartLoad();
    });

    test('should switch to Fibonacci mode and display Fibonacci controls', async () => {
        // Requirement 3.1: WHEN user selects Fibonacci mode THEN system SHALL display Fibonacci analysis tools
        await chartPage.selectChartMode('fibonacci');
        
        // Verify mode is selected
        expect(await chartPage.getSelectedChartMode()).toBe('fib');
        
        // Verify chart updates with new mode
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
    });

    test('should switch to RSI mode and display RSI indicator', async () => {
        // Requirement 3.2: WHEN user selects RSI mode THEN system SHALL display RSI technical indicator
        await chartPage.selectChartMode('rsi');
        
        // Verify mode is selected
        expect(await chartPage.getSelectedChartMode()).toBe('rsi');
        
        // Verify chart updates with RSI mode
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
    });

    test('should switch to MACD mode and display MACD indicator', async () => {
        // Requirement 3.2: WHEN user selects MACD mode THEN system SHALL display MACD technical indicator
        await chartPage.selectChartMode('macd');
        
        // Verify mode is selected
        expect(await chartPage.getSelectedChartMode()).toBe('macd');
        
        // Verify chart updates with MACD mode
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
    });
});