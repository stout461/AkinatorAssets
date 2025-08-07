import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { LoginPage } from './LoginPage';
import { TestDataManager } from '../utils/TestDataManager';

export class DashboardPage extends BasePage {
    // Essential selectors for dashboard functionality
    private readonly tickerInput: Locator;
    private readonly submitButton: Locator;
    private readonly periodButtons: Locator;
    private readonly chartContainer: Locator;
    private readonly chartLoadingIndicator: Locator;
    private readonly chartErrorMessage: Locator;
    private readonly detailedGraphButton: Locator;
    private readonly analysisContainer: Locator;
    private readonly errorMessage: Locator;

    constructor(page: Page) {
        super(page);
        
        // Initialize selectors based on the HTML structure
        this.tickerInput = page.locator('#ticker');
        this.submitButton = page.locator('#submit');
        this.periodButtons = page.locator('input[name="period"]');
        this.chartContainer = page.locator('#graph');
        this.chartLoadingIndicator = page.locator('#chart-loading');
        this.chartErrorMessage = page.locator('#chart-error');
        this.detailedGraphButton = page.locator('#detailed-graph-btn');
        this.analysisContainer = page.locator('#analysis-container');
        this.errorMessage = page.locator('#error');
    }

    async navigateTo(): Promise<void> {
        await this.page.goto('/');
        await this.waitForPageLoad();
    }

    async waitForPageLoad(): Promise<void> {
        // Wait for essential dashboard elements to be visible
        await expect(this.tickerInput).toBeVisible();
        await expect(this.submitButton).toBeVisible();
        await expect(this.periodButtons.first()).toBeVisible();
    }

    async enterTicker(symbol: string): Promise<void> {
        await this.tickerInput.clear();
        await this.tickerInput.fill(symbol);
    }

    async clickSubmit(): Promise<void> {
        await this.submitButton.click();
    }

    async selectPeriod(period: string): Promise<void> {
        // Click the label instead of the radio button to avoid interception issues
        const periodLabel = this.page.locator(`label[for="period${period}"]`);
        await periodLabel.click();
    }

    async waitForChartLoad(): Promise<void> {
        // Wait for any loading to complete - loading indicator might appear briefly or not at all
        try {
            // Try to wait for loading indicator, but don't fail if it doesn't appear
            await expect(this.chartLoadingIndicator).toBeVisible({ timeout: 2000 });
            await expect(this.chartLoadingIndicator).toBeHidden({ timeout: 30000 });
        } catch {
            // Loading indicator might not appear if data loads very quickly
            console.log('Loading indicator not detected - checking for chart content directly');
        }
        
        // Wait for chart container to have content (more reliable)
        await expect(this.chartContainer).toBeVisible();
        
        // Wait for the chart to actually render (look for plotly content)
        await this.page.waitForFunction(() => {
            const chartElement = document.querySelector('#graph');
            return chartElement && (
                chartElement.querySelector('.plotly-graph-div') !== null ||
                chartElement.querySelector('svg') !== null ||
                chartElement.innerHTML.trim().length > 100
            );
        }, { timeout: 30000 });
    }

    async isChartVisible(): Promise<boolean> {
        return await this.chartContainer.isVisible();
    }

    async isChartLoading(): Promise<boolean> {
        return await this.chartLoadingIndicator.isVisible();
    }

    async getChartErrorMessage(): Promise<string | null> {
        if (await this.chartErrorMessage.isVisible()) {
            return await this.chartErrorMessage.textContent();
        }
        return null;
    }

    async getSelectedPeriod(): Promise<string | null> {
        // Look for checked radio button
        const checkedPeriod = this.page.locator('input[name="period"]:checked');
        if (await checkedPeriod.count() > 0) {
            return await checkedPeriod.getAttribute('value');
        }
        return null;
    }

    async getTickerValue(): Promise<string> {
        return await this.tickerInput.inputValue();
    }

    async navigateToDetailedView(): Promise<void> {
        await this.detailedGraphButton.click();
    }

    async isDetailedGraphButtonVisible(): Promise<boolean> {
        return await this.detailedGraphButton.isVisible();
    }

    async isAnalysisContainerVisible(): Promise<boolean> {
        return await this.analysisContainer.isVisible();
    }

    async getErrorMessage(): Promise<string | null> {
        if (await this.errorMessage.isVisible()) {
            return await this.errorMessage.textContent();
        }
        return null;
    }

    // Helper method to perform complete ticker entry and chart loading
    async loadStockData(ticker: string, period: string = '1Y'): Promise<void> {
        await this.enterTicker(ticker);
        await this.selectPeriod(period);
        await this.clickSubmit();
        await this.waitForChartLoad();
    }

    // Verify chart has loaded successfully
    async verifyChartLoaded(): Promise<void> {
        await expect(this.chartContainer).toBeVisible();
        await expect(this.chartLoadingIndicator).toBeHidden();
        
        // Verify chart has actual content - look for SVG or substantial content
        await this.page.waitForFunction(() => {
            const chartElement = document.querySelector('#graph');
            if (!chartElement) return false;
            
            // Check for SVG content (Plotly charts use SVG)
            const hasSVG = chartElement.querySelector('svg') !== null;
            
            // Check for substantial content (more than just empty div)
            const hasContent = chartElement.innerHTML.trim().length > 1000;
            
            // Check for plotly-specific classes
            const hasPlotlyContent = chartElement.querySelector('.plot-container') !== null ||
                                   chartElement.querySelector('.svg-container') !== null;
            
            return hasSVG || (hasContent && hasPlotlyContent);
        }, { timeout: 10000 });
    }
}