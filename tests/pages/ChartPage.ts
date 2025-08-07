import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object Model for Chart Interaction functionality
 * Handles detailed chart view with technical analysis features
 */
export class ChartPage extends BasePage {
    // Chart container and controls
    private readonly chartContainer: Locator;
    private readonly chartSettingsToggle: Locator;
    private readonly chartSettings: Locator;
    private readonly chartLoadingIndicator: Locator;
    private readonly chartErrorMessage: Locator;

    // Analysis mode selectors (radio buttons)
    private readonly fibonacciModeButton: Locator;
    private readonly trendlinesModeButton: Locator;
    private readonly elliottModeButton: Locator;
    private readonly rsiModeButton: Locator;
    private readonly macdModeButton: Locator;
    private readonly volumeModeButton: Locator;
    private readonly candlestickModeButton: Locator;
    private readonly movingAverageModeButton: Locator;

    // Technical indicator toggles
    private readonly showRSIToggle: Locator;
    private readonly showMACDToggle: Locator;
    private readonly showVolumeToggle: Locator;
    private readonly showCandlestickToggle: Locator;

    // Moving average controls
    private readonly ma5Toggle: Locator;
    private readonly ma10Toggle: Locator;
    private readonly ma20Toggle: Locator;
    private readonly ma50Toggle: Locator;
    private readonly ma100Toggle: Locator;
    private readonly ma200Toggle: Locator;
    private readonly customMAInput: Locator;
    private readonly addCustomMAButton: Locator;

    // Fibonacci controls
    private readonly showFibToggle: Locator;
    private readonly manualFibToggle: Locator;
    private readonly showExtensionsToggle: Locator;
    private readonly fibHighValueInput: Locator;

    // Navigation controls
    private readonly backToDashboardButton: Locator;
    private readonly tickerInput: Locator;
    private readonly updateChartButton: Locator;

    constructor(page: Page) {
        super(page);
        
        // Initialize chart container and main controls
        this.chartContainer = page.locator('#detailed-graph');
        this.chartSettingsToggle = page.locator('#chart-settings-toggle');
        this.chartSettings = page.locator('#chart-settings');
        this.chartLoadingIndicator = page.locator('#chart-loading');
        this.chartErrorMessage = page.locator('#chart-error');

        // Initialize analysis mode buttons
        this.fibonacciModeButton = page.locator('#fibMode');
        this.trendlinesModeButton = page.locator('#trendlinesMode');
        this.elliottModeButton = page.locator('#elliottMode');
        this.rsiModeButton = page.locator('#rsiMode');
        this.macdModeButton = page.locator('#macdMode');
        this.volumeModeButton = page.locator('#volumeMode');
        this.candlestickModeButton = page.locator('#candlestickMode');
        this.movingAverageModeButton = page.locator('#maMode');

        // Initialize technical indicator toggles
        this.showRSIToggle = page.locator('#showRSI');
        this.showMACDToggle = page.locator('#showMACD');
        this.showVolumeToggle = page.locator('#showVolume');
        this.showCandlestickToggle = page.locator('#showCandlestick');

        // Initialize moving average controls
        this.ma5Toggle = page.locator('#ma-5');
        this.ma10Toggle = page.locator('#ma-10');
        this.ma20Toggle = page.locator('#ma-20');
        this.ma50Toggle = page.locator('#ma-50');
        this.ma100Toggle = page.locator('#ma-100');
        this.ma200Toggle = page.locator('#ma-200');
        this.customMAInput = page.locator('#custom-ma-input');
        this.addCustomMAButton = page.locator('#add-custom-ma');

        // Initialize Fibonacci controls
        this.showFibToggle = page.locator('#showFib');
        this.manualFibToggle = page.locator('#manualFibMode');
        this.showExtensionsToggle = page.locator('#showExtensions');
        this.fibHighValueInput = page.locator('#fibHighValue');

        // Initialize navigation controls
        this.backToDashboardButton = page.locator('#back-to-dashboard-btn');
        this.tickerInput = page.locator('#ticker');
        this.updateChartButton = page.locator('#update-chart');
    }

    async waitForPageLoad(): Promise<void> {
        // Wait for essential chart elements to be visible
        await expect(this.chartContainer).toBeVisible();
        await expect(this.tickerInput).toBeVisible();
        await expect(this.updateChartButton).toBeVisible();
    }

    async navigateToDetailedChart(ticker: string = 'AAPL', period: string = '1Y'): Promise<void> {
        await this.navigateTo(`/detailed-graph/${ticker}?period=${period}`);
    }

    async openChartSettings(): Promise<void> {
        const isVisible = await this.chartSettings.isVisible();
        if (!isVisible) {
            await this.chartSettingsToggle.click();
            await expect(this.chartSettings).toBeVisible({ timeout: 5000 });
            // Wait for settings animation to complete
            await this.page.waitForTimeout(500);
        }
    }

    async closeChartSettings(): Promise<void> {
        const isVisible = await this.chartSettings.isVisible();
        if (isVisible) {
            await this.chartSettingsToggle.click();
            await expect(this.chartSettings).toBeHidden();
        }
    }

    // Chart Mode Selection Methods
    async selectChartMode(mode: 'fibonacci' | 'trendlines' | 'elliott' | 'rsi' | 'macd' | 'volume' | 'candlestick' | 'ma'): Promise<void> {
        await this.openChartSettings();
        
        const modeLabels = {
            fibonacci: 'label[for="fibMode"]',
            trendlines: 'label[for="trendlinesMode"]',
            elliott: 'label[for="elliottMode"]',
            rsi: 'label[for="rsiMode"]',
            macd: 'label[for="macdMode"]',
            volume: 'label[for="volumeMode"]',
            candlestick: 'label[for="candlestickMode"]',
            ma: 'label[for="maMode"]'
        };

        const labelSelector = modeLabels[mode];
        if (labelSelector) {
            const label = this.page.locator(labelSelector);
            await label.click();
            // Wait for mode to be applied
            await this.page.waitForTimeout(500);
        }
    }

    async getSelectedChartMode(): Promise<string | null> {
        const checkedMode = this.page.locator('input[name="analysisMode"]:checked');
        if (await checkedMode.count() > 0) {
            return await checkedMode.getAttribute('value');
        }
        return null;
    }

    // Technical Indicator Methods
    async toggleTechnicalIndicator(indicator: 'rsi' | 'macd' | 'volume' | 'candlestick', enabled: boolean): Promise<void> {
        await this.openChartSettings();
        
        // First switch to the appropriate mode to make the toggle visible
        const modeMap = {
            rsi: 'rsi',
            macd: 'macd', 
            volume: 'volume',
            candlestick: 'candlestick'
        };
        
        await this.selectChartMode(modeMap[indicator] as any);
        
        // Wait for the mode content to be visible
        await this.page.waitForTimeout(500);
        
        // Use the compact toggle wrapper instead of direct checkbox
        const toggleWrappers = {
            rsi: this.page.locator('.compact-toggle:has(#showRSI)'),
            macd: this.page.locator('.compact-toggle:has(#showMACD)'),
            volume: this.page.locator('.compact-toggle:has(#showVolume)'),
            candlestick: this.page.locator('.compact-toggle:has(#showCandlestick)')
        };

        const toggleWrapper = toggleWrappers[indicator];
        const directToggle = {
            rsi: this.showRSIToggle,
            macd: this.showMACDToggle,
            volume: this.showVolumeToggle,
            candlestick: this.showCandlestickToggle
        }[indicator];

        if (toggleWrapper && await toggleWrapper.isVisible()) {
            const isCurrentlyChecked = await directToggle.isChecked();
            if (isCurrentlyChecked !== enabled) {
                await toggleWrapper.click();
            }
        } else if (directToggle && await directToggle.isVisible()) {
            const isCurrentlyChecked = await directToggle.isChecked();
            if (isCurrentlyChecked !== enabled) {
                await directToggle.click();
            }
        }
    }

    async isTechnicalIndicatorEnabled(indicator: 'rsi' | 'macd' | 'volume' | 'candlestick'): Promise<boolean> {
        const toggles = {
            rsi: this.showRSIToggle,
            macd: this.showMACDToggle,
            volume: this.showVolumeToggle,
            candlestick: this.showCandlestickToggle
        };

        const toggle = toggles[indicator];
        return toggle ? await toggle.isChecked() : false;
    }

    // Moving Average Methods
    async toggleMovingAverage(period: 5 | 10 | 20 | 50 | 100 | 200, enabled: boolean): Promise<void> {
        await this.openChartSettings();
        await this.selectChartMode('ma'); // Switch to MA mode first
        
        // Wait for MA mode content to be visible
        await this.page.waitForTimeout(500);
        
        // Use the ma-toggle-mini wrapper instead of direct checkbox
        const toggleWrappers = {
            5: this.page.locator('.ma-toggle-mini:has(#ma-5)'),
            10: this.page.locator('.ma-toggle-mini:has(#ma-10)'),
            20: this.page.locator('.ma-toggle-mini:has(#ma-20)'),
            50: this.page.locator('.ma-toggle-mini:has(#ma-50)'),
            100: this.page.locator('.ma-toggle-mini:has(#ma-100)'),
            200: this.page.locator('.ma-toggle-mini:has(#ma-200)')
        };

        const toggles = {
            5: this.ma5Toggle,
            10: this.ma10Toggle,
            20: this.ma20Toggle,
            50: this.ma50Toggle,
            100: this.ma100Toggle,
            200: this.ma200Toggle
        };

        const toggleWrapper = toggleWrappers[period];
        const toggle = toggles[period];
        
        if (toggleWrapper && await toggleWrapper.isVisible()) {
            const isCurrentlyChecked = await toggle.isChecked();
            if (isCurrentlyChecked !== enabled) {
                await toggleWrapper.click();
            }
        } else if (toggle && await toggle.isVisible()) {
            const isCurrentlyChecked = await toggle.isChecked();
            if (isCurrentlyChecked !== enabled) {
                await toggle.click();
            }
        }
    }

    async addCustomMovingAverage(period: number): Promise<void> {
        await this.openChartSettings();
        await this.selectChartMode('ma');
        
        await this.customMAInput.fill(period.toString());
        await this.addCustomMAButton.click();
        
        // Wait for the custom MA to be added
        await this.page.waitForTimeout(500);
    }

    async isMovingAverageEnabled(period: 5 | 10 | 20 | 50 | 100 | 200): Promise<boolean> {
        const toggles = {
            5: this.ma5Toggle,
            10: this.ma10Toggle,
            20: this.ma20Toggle,
            50: this.ma50Toggle,
            100: this.ma100Toggle,
            200: this.ma200Toggle
        };

        const toggle = toggles[period];
        return toggle ? await toggle.isChecked() : false;
    }

    // Fibonacci Methods
    async toggleFibonacci(enabled: boolean): Promise<void> {
        await this.openChartSettings();
        await this.selectChartMode('fibonacci');
        
        // Wait for fibonacci mode content to be visible
        await this.page.waitForTimeout(500);
        
        // Use the compact toggle wrapper for Fibonacci
        const fibToggleWrapper = this.page.locator('.compact-toggle:has(#showFib)');
        
        if (await fibToggleWrapper.isVisible()) {
            const isCurrentlyChecked = await this.showFibToggle.isChecked();
            if (isCurrentlyChecked !== enabled) {
                await fibToggleWrapper.click();
            }
        } else if (await this.showFibToggle.isVisible()) {
            const isCurrentlyChecked = await this.showFibToggle.isChecked();
            if (isCurrentlyChecked !== enabled) {
                await this.showFibToggle.click();
            }
        }
    }

    async isFibonacciEnabled(): Promise<boolean> {
        return await this.showFibToggle.isChecked();
    }

    // Chart Interaction Methods
    async waitForChartLoad(): Promise<void> {
        // Wait for loading to complete
        try {
            await expect(this.chartLoadingIndicator).toBeVisible({ timeout: 2000 });
            await expect(this.chartLoadingIndicator).toBeHidden({ timeout: 30000 });
        } catch {
            // Loading might be too fast to detect
        }
        
        // Wait for chart content to be rendered
        await this.page.waitForFunction(() => {
            const chartElement = document.querySelector('#detailed-graph');
            return chartElement && (
                chartElement.querySelector('svg') !== null ||
                chartElement.innerHTML.trim().length > 1000
            );
        }, { timeout: 30000 });
    }

    async verifyChartLoaded(): Promise<void> {
        await expect(this.chartContainer).toBeVisible();
        
        // Verify chart has actual content
        await this.page.waitForFunction(() => {
            const chartElement = document.querySelector('#detailed-graph');
            if (!chartElement) return false;
            
            const hasSVG = chartElement.querySelector('svg') !== null;
            const hasContent = chartElement.innerHTML.trim().length > 1000;
            const hasPlotlyContent = chartElement.querySelector('.plot-container') !== null ||
                                   chartElement.querySelector('.svg-container') !== null;
            
            return hasSVG || (hasContent && hasPlotlyContent);
        }, { timeout: 10000 });
    }

    async updateChart(): Promise<void> {
        await this.updateChartButton.click();
        await this.waitForChartLoad();
    }

    async enterTicker(ticker: string): Promise<void> {
        await this.tickerInput.clear();
        await this.tickerInput.fill(ticker);
    }

    async getTickerValue(): Promise<string> {
        return await this.tickerInput.inputValue();
    }

    async navigateBackToDashboard(): Promise<void> {
        await this.backToDashboardButton.click();
    }

    async isChartVisible(): Promise<boolean> {
        return await this.chartContainer.isVisible();
    }

    async getChartErrorMessage(): Promise<string | null> {
        if (await this.chartErrorMessage.isVisible()) {
            return await this.chartErrorMessage.textContent();
        }
        return null;
    }

    // Multiple indicators test helper
    async enableMultipleIndicators(indicators: Array<'rsi' | 'macd' | 'volume' | 'candlestick'>): Promise<void> {
        for (const indicator of indicators) {
            await this.toggleTechnicalIndicator(indicator, true);
        }
        await this.updateChart();
    }

    async verifyMultipleIndicatorsEnabled(indicators: Array<'rsi' | 'macd' | 'volume' | 'candlestick'>): Promise<void> {
        for (const indicator of indicators) {
            const isEnabled = await this.isTechnicalIndicatorEnabled(indicator);
            expect(isEnabled).toBe(true);
        }
    }

    // Keyboard shortcut methods
    async pressKeyboardShortcut(key: string): Promise<void> {
        await this.page.keyboard.press(key);
        await this.page.waitForTimeout(500); // Wait for shortcut to take effect
    }
}