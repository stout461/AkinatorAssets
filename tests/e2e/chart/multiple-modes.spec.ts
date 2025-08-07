import { test, expect } from '../../fixtures/fast-auth-fixtures';
import { ChartPage } from '../../pages/ChartPage';
import { TestDataManager } from '../../utils/TestDataManager';

test.describe('Multiple Modes Simultaneously', () => {
    let chartPage: ChartPage;
    const ticker = TestDataManager.getValidTickers()[0]; // AAPL

    test.beforeEach(async ({ authenticatedPage }) => {
        // Use pre-authenticated page - no login needed!
        chartPage = new ChartPage(authenticatedPage);
        await chartPage.navigateToDetailedChart(ticker);
        await chartPage.waitForPageLoad();
        await chartPage.waitForChartLoad();
    });

    test('should display multiple technical indicators simultaneously', async () => {
        // Requirement 3.5: WHEN user enables multiple indicators THEN system SHALL display all selected indicators together
        
        const indicators: Array<'rsi' | 'macd' | 'volume'> = ['rsi', 'macd', 'volume'];
        
        // Enable multiple indicators
        await chartPage.enableMultipleIndicators(indicators);
        
        // Verify all indicators are enabled
        await chartPage.verifyMultipleIndicatorsEnabled(indicators);
        
        // Verify chart loads with all indicators
        await chartPage.verifyChartLoaded();
    });

    test('should combine moving averages with technical indicators', async () => {
        // Requirement 3.5: WHEN user combines MA with indicators THEN system SHALL display both overlays
        
        // Enable moving averages
        await chartPage.toggleMovingAverage(20, true);
        await chartPage.toggleMovingAverage(50, true);
        
        // Enable technical indicators
        await chartPage.toggleTechnicalIndicator('rsi', true);
        await chartPage.toggleTechnicalIndicator('volume', true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Verify all are still enabled
        expect(await chartPage.isMovingAverageEnabled(20)).toBe(true);
        expect(await chartPage.isMovingAverageEnabled(50)).toBe(true);
        expect(await chartPage.isTechnicalIndicatorEnabled('rsi')).toBe(true);
        expect(await chartPage.isTechnicalIndicatorEnabled('volume')).toBe(true);
    });

    test('should combine Fibonacci with other indicators', async () => {
        // Requirement 3.5: WHEN user enables Fibonacci with other indicators THEN system SHALL display combined analysis
        
        // Enable Fibonacci
        await chartPage.toggleFibonacci(true);
        
        // Enable other indicators
        await chartPage.toggleTechnicalIndicator('macd', true);
        await chartPage.toggleMovingAverage(200, true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Verify all are enabled
        expect(await chartPage.isFibonacciEnabled()).toBe(true);
        expect(await chartPage.isTechnicalIndicatorEnabled('macd')).toBe(true);
        expect(await chartPage.isMovingAverageEnabled(200)).toBe(true);
    });
});