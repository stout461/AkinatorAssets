import { test, expect } from '../../fixtures/fast-auth-fixtures';
import { ChartPage } from '../../pages/ChartPage';
import { TestDataManager } from '../../utils/TestDataManager';

test.describe('Technical Indicators', () => {
    let chartPage: ChartPage;
    const ticker = TestDataManager.getValidTickers()[0]; // AAPL

    test.beforeEach(async ({ authenticatedPage }) => {
        // Use pre-authenticated page - no login needed!
        chartPage = new ChartPage(authenticatedPage);
        await chartPage.navigateToDetailedChart(ticker);
        await chartPage.waitForPageLoad();
        await chartPage.waitForChartLoad();
    });

    test('should toggle RSI indicator on and off', async () => {
        // Requirement 3.3: WHEN user toggles RSI indicator THEN system SHALL show/hide RSI overlay
        
        // Enable RSI indicator
        await chartPage.toggleTechnicalIndicator('rsi', true);
        expect(await chartPage.isTechnicalIndicatorEnabled('rsi')).toBe(true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Disable RSI indicator
        await chartPage.toggleTechnicalIndicator('rsi', false);
        expect(await chartPage.isTechnicalIndicatorEnabled('rsi')).toBe(false);
    });

    test('should toggle MACD indicator on and off', async () => {
        // Requirement 3.3: WHEN user toggles MACD indicator THEN system SHALL show/hide MACD overlay
        
        // Enable MACD indicator
        await chartPage.toggleTechnicalIndicator('macd', true);
        expect(await chartPage.isTechnicalIndicatorEnabled('macd')).toBe(true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Disable MACD indicator
        await chartPage.toggleTechnicalIndicator('macd', false);
        expect(await chartPage.isTechnicalIndicatorEnabled('macd')).toBe(false);
    });

    test('should toggle Volume indicator on and off', async () => {
        // Requirement 3.3: WHEN user toggles Volume indicator THEN system SHALL show/hide Volume bars
        
        // Enable Volume indicator
        await chartPage.toggleTechnicalIndicator('volume', true);
        expect(await chartPage.isTechnicalIndicatorEnabled('volume')).toBe(true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Disable Volume indicator
        await chartPage.toggleTechnicalIndicator('volume', false);
        expect(await chartPage.isTechnicalIndicatorEnabled('volume')).toBe(false);
    });

    test('should toggle Candlestick view on and off', async () => {
        // Requirement 3.3: WHEN user toggles Candlestick view THEN system SHALL switch between line and candlestick chart
        
        // Enable Candlestick view
        await chartPage.toggleTechnicalIndicator('candlestick', true);
        expect(await chartPage.isTechnicalIndicatorEnabled('candlestick')).toBe(true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Disable Candlestick view
        await chartPage.toggleTechnicalIndicator('candlestick', false);
        expect(await chartPage.isTechnicalIndicatorEnabled('candlestick')).toBe(false);
    });
});