import { test, expect } from '../../fixtures/fast-auth-fixtures';
import { ChartPage } from '../../pages/ChartPage';
import { TestDataManager } from '../../utils/TestDataManager';

test.describe('Moving Averages', () => {
    let chartPage: ChartPage;
    const ticker = TestDataManager.getValidTickers()[0]; // AAPL

    test.beforeEach(async ({ authenticatedPage }) => {
        // Use pre-authenticated page - no login needed!
        chartPage = new ChartPage(authenticatedPage);
        await chartPage.navigateToDetailedChart(ticker);
        await chartPage.waitForPageLoad();
        await chartPage.waitForChartLoad();
    });

    test('should enable and disable standard moving averages', async () => {
        // Requirement 3.4: WHEN user selects moving averages THEN system SHALL display MA lines on chart
        
        // Test 20-day moving average
        await chartPage.toggleMovingAverage(20, true);
        expect(await chartPage.isMovingAverageEnabled(20)).toBe(true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
        
        // Disable 20-day moving average
        await chartPage.toggleMovingAverage(20, false);
        expect(await chartPage.isMovingAverageEnabled(20)).toBe(false);
    });

    test('should enable multiple moving averages simultaneously', async () => {
        // Requirement 3.4: WHEN user selects multiple moving averages THEN system SHALL display all selected MA lines
        
        // Enable multiple moving averages
        await chartPage.toggleMovingAverage(50, true);
        await chartPage.toggleMovingAverage(200, true);
        
        // Verify both are enabled
        expect(await chartPage.isMovingAverageEnabled(50)).toBe(true);
        expect(await chartPage.isMovingAverageEnabled(200)).toBe(true);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
    });

    test('should add custom moving average period', async () => {
        // Requirement 3.4: WHEN user adds custom MA period THEN system SHALL display custom MA line
        
        // Add custom 30-day moving average
        await chartPage.addCustomMovingAverage(30);
        
        await chartPage.updateChart();
        await chartPage.verifyChartLoaded();
    });
});