console.log("✅ chart.js loaded");

// Constants (extracted for easy tweaking)
const DEFAULT_COLORS = ['#FF5733', '#33FFCC', '#FF33A6', '#3371FF', '#FFD633', '#4CAF50'];
const API_ENDPOINT = '/plot';

// Sub-class: Base Mode Handler (Strategy Pattern)
class BaseModeHandler {
    constructor(chart) {
        this.chart = chart;
    }
    handleClick(data) { } // Override per mode
    getParams() { return {}; } // Mode-specific fetch params
    // Add more hooks as needed
}

// Sub-class: Fibonacci Mode Handler
class FibModeHandler extends BaseModeHandler {
    handleClick(data) {
        const clickedY = data.points[0].y;
        this.chart.handleFibonacciClick(clickedY);
    }
}

// Sub-class: Trendlines Mode Handler
class TrendlineModeHandler extends BaseModeHandler {
    handleClick(data) {
        this.chart.handleTrendlineClick(data);
    }
}

// Sub-class: Elliott Mode Handler
class ElliottModeHandler extends BaseModeHandler {
    handleClick(data) {
        const clickedX = data.points[0].x;
        const clickedY = data.points[0].y.toFixed(2);
        this.chart.state.elliottPoints.push({ x: clickedX, y: clickedY });
        this.chart.ui.updateElliottDisplay(this.chart.state.elliottPoints);
        this.chart.loadChartData(true); // Refresh chart
    }
}

// Sub-class: UI Manager
class ChartUI {
    constructor(chart) {
        this.chart = chart;
        this.containerId = chart.containerId;
    }

    showLoading() {
        $(`#${this.containerId}-loading, #chart-loading`).show();
    }

    hideLoading() {
        $(`#${this.containerId}-loading, #chart-loading`).hide();
    }

    showError(message) {
        $(`#${this.containerId}-error, #chart-error`).text(message).show();
    }

    hideError() {
        $(`#${this.containerId}-error, #chart-error`).hide();
    }

    updateElliottDisplay(points) {
        const grid = $('#elliott-points-grid');
        const countSpan = $('#elliott-points-count');

        console.log('Updating Elliott display with points:', points);

        // Update points count
        countSpan.text(points.length);

        // Update points grid
        grid.empty();
        points.forEach((p, i) => {
            const pointChip = $(`
                <div class="elliott-point-chip">
                    <span class="point-label">${i}</span>
                    <span class="point-value">${parseFloat(p.y).toFixed(1)}</span>
                    <button class="remove-point" data-index="${i}" title="Remove point">×</button>
                </div>
            `);
            grid.append(pointChip);
        });
    }

    updateIndicatorVisualState() {
        // Update RSI indicator visual state
        const rsiEnabled = $('#showRSI').is(':checked');
        const rsiTab = $('label[for="rsiMode"]');

        if (rsiEnabled) {
            rsiTab.addClass('indicator-active');
        } else {
            rsiTab.removeClass('indicator-active');
        }

        // Update MACD indicator visual state
        const macdEnabled = $('#showMACD').is(':checked');
        const macdTab = $('label[for="macdMode"]');

        if (macdEnabled) {
            macdTab.addClass('indicator-active');
        } else {
            macdTab.removeClass('indicator-active');
        }

        // Update Volume indicator visual state
        const volumeEnabled = $('#showVolume').is(':checked');
        const volumeTab = $('label[for="volumeMode"]');

        if (volumeEnabled) {
            volumeTab.addClass('indicator-active');
        } else {
            volumeTab.removeClass('indicator-active');
        }

        // Update Candlestick indicator visual state
        const candlestickEnabled = $('#showCandlestick').is(':checked');
        const candlestickTab = $('label[for="candlestickMode"]');

        if (candlestickEnabled) {
            candlestickTab.addClass('indicator-active');
        } else {
            candlestickTab.removeClass('indicator-active');
        }

        console.log(`📊 Indicator states updated - RSI: ${rsiEnabled}, MACD: ${macdEnabled}, Volume: ${volumeEnabled}, Candlestick: ${candlestickEnabled}`);
    }

    updateCustomMADisplay(customMAs) {
        const customMAList = $('#custom-ma-display');
        customMAList.empty();

        if (customMAs.length === 0) {
            customMAList.hide();
            return;
        }

        customMAList.show();

        customMAs.forEach((period) => {
            const tag = $(`
                <span class="custom-ma-tag">
                    MA${period}
                    <span class="remove-custom-ma" data-period="${period}">×</span>
                </span>
            `);
            customMAList.append(tag);
        });
    }

    updateSettingsVisibility(mode) {
        // Hide all mode content sections
        $('.mode-content').removeClass('active');

        // Show the appropriate mode content
        if (mode === 'fib') {
            $('#fibSettings').addClass('active');
        } else if (mode === 'trendlines') {
            $('#trendLineSettings').addClass('active');
        } else if (mode === 'elliott') {
            $('#elliott-settings').addClass('active');
            this.updateElliottDisplay(this.chart.state.elliottPoints);
        } else if (mode === 'rsi') {
            $('#rsiSettings').addClass('active');
        } else if (mode === 'macd') {
            $('#macdSettings').addClass('active');
        } else if (mode === 'volume') {
            $('#volumeSettings').addClass('active');
        } else if (mode === 'candlestick') {
            $('#candlestickSettings').addClass('active');
        } else if (mode === 'ma') {
            $('#maSettings').addClass('active');
        }
    }

    toggleSettings() {
        const settings = $('#chart-settings');
        const button = $('#chart-settings-toggle');

        settings.slideToggle(300, function () {
            // Update button text after animation completes
            if (settings.is(':visible')) {
                button.text('Hide Settings');
            } else {
                button.text('Settings');
            }
        });

        console.log('Settings toggled, visible:', settings.is(':visible'));
    }
}

// Sub-class: State Manager
class ChartStateManager {
    constructor() {
        this.chartDataX = [];
        this.pointForLine = null;
        this.trendLineCount = 0;
        this.customMAs = [];
        this.elliottPoints = [];
        this.trendLines = []; // Store persistent trendlines
    }

    restoreTrendlines(containerId) {
        // Re-add all stored trendlines to the chart
        this.trendLines.forEach(trendLine => {
            try {
                Plotly.addTraces(containerId, trendLine.trace);
            } catch (error) {
                console.warn('Failed to restore trendline:', trendLine.id, error);
            }
        });

        if (this.trendLines.length > 0) {
            console.log(`📈 Restored ${this.trendLines.length} persistent trendlines`);
        }
    }

    clearAllTrendlines() {
        this.trendLines = [];
        this.trendLineCount = 0;
        this.pointForLine = null;
        console.log('📈 Cleared all trendlines');
    }

    addCustomMovingAverage(period) {
        if (period && period > 0 && period <= 500) {
            if (!this.customMAs.includes(period)) {
                this.customMAs.push(period);
                return true;
            } else {
                alert('This moving average period is already added.');
                return false;
            }
        } else {
            alert('Please enter a valid period between 1 and 500.');
            return false;
        }
    }

    removeCustomMovingAverage(period) {
        const index = this.customMAs.indexOf(period);
        if (index > -1) {
            this.customMAs.splice(index, 1);
            return true;
        }
        return false;
    }

    getState() {
        return {
            customMAs: [...this.customMAs],
            elliottPoints: [...this.elliottPoints],
            trendLines: [...this.trendLines],
            // Add more as needed
        };
    }

    restoreState(state) {
        if (state.customMAs) this.customMAs = [...state.customMAs];
        if (state.elliottPoints) this.elliottPoints = [...state.elliottPoints];
        if (state.trendLines) this.trendLines = [...state.trendLines];
        // Add more as needed
    }
}

// Main Class
class StockChart {
    constructor(containerId, mode = 'compact') {
        this.containerId = containerId;
        this.mode = mode; // 'compact' or 'detailed'
        this.ui = new ChartUI(this);
        this.state = new ChartStateManager();
        this.modes = { // Strategy map for interactive modes
            fib: new FibModeHandler(this),
            trendlines: new TrendlineModeHandler(this),
            elliott: new ElliottModeHandler(this),
            // Non-interactive modes (rsi, macd, ma) handled separately
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        console.log(`📊 StockChart initialized in ${this.mode} mode for container: ${this.containerId}`);
    }

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    getChartClickMode() {
        const analysisMode = $('input[name="analysisMode"]:checked').val();
        // Map analysis modes to chart click modes for backend compatibility
        if (analysisMode === 'rsi' || analysisMode === 'macd' || analysisMode === 'ma' ||
            analysisMode === 'volume' || analysisMode === 'candlestick') {
            return 'fib'; // Default click mode for indicator modes
        }
        return analysisMode;
    }

    getAnalysisMode() {
        return $('input[name="analysisMode"]:checked').val();
    }

    randomColor() {
        return DEFAULT_COLORS[Math.floor(Math.random() * DEFAULT_COLORS.length)];
    }

    getSelectedMovingAverages() {
        const selectedMAs = [];

        // Get checked standard MAs
        $('.ma-checkbox:checked').each(function () {
            selectedMAs.push(parseInt($(this).val()));
        });

        // Add custom MAs
        this.state.customMAs.forEach(function (period) {
            selectedMAs.push(period);
        });

        // Remove duplicates and sort
        return [...new Set(selectedMAs)].sort((a, b) => a - b);
    }

    getCommonFetchParams() {
        const ticker = $('#ticker').val().trim();
        const period = $('input[name="period"]:checked').val();
        const chartMode = this.getChartClickMode();
        // Fibonacci settings - Always send if configured (persist across modes)
        const manualFib = $('#manualFibMode').is(':checked');
        const showExtensions = $('#showExtensions').is(':checked');
        const fibHigh = $('#fibHighValue').val();
        const showFib = $('#showFib').is(':checked');
        const showVolume = $('#showVolume').is(':checked');
        const showCandlestick = $('#showCandlestick').is(':checked');

        // Moving Averages - Always send if configured (persist across modes)
        const selectedMAs = this.getSelectedMovingAverages();
        const movingAveragesParam = selectedMAs.length > 0 ? selectedMAs.join(',') : '';

        // Elliott Wave Support - Always send points if they exist (persist across modes)
        const elliottPointsParam = (this.state.elliottPoints.length > 0) ?
            JSON.stringify(this.state.elliottPoints) : '';

        // Elliott Wave Auto-generation toggle
        const showElliottAutoWaves = $('#show-elliott-auto-waves').is(':checked');

        // NEW: Technical Indicators
        const showRSI = $('#showRSI').is(':checked');
        const showMACD = $('#showMACD').is(':checked');

        // Include mode-specific params if any
        const modeHandler = this.modes[chartMode];
        const modeParams = modeHandler ? modeHandler.getParams() : {};

        return {
            ticker,
            period,
            chartMode,
            manualFib,
            showExtensions,
            fibHigh,
            movingAverages: movingAveragesParam,
            showFib,
            elliott_points: elliottPointsParam,
            show_elliott_auto_waves: showElliottAutoWaves,
            showRSI: showRSI,
            showMACD: showMACD,
            showVolume: showVolume,
            showCandlestick: showCandlestick,
            ...modeParams
        };
    }

    // ========================================
    // CHART DATA AND RENDERING
    // ========================================

    async loadChartData(onlyChart = false) {
        const params = this.getCommonFetchParams();

        if (!params.ticker) {
            this.ui.showError('Please enter a valid ticker symbol');
            return Promise.reject('Invalid ticker');
        }

        this.ui.showLoading();
        this.ui.hideError();

        params.includeFinancials = onlyChart ? 'false' : 'true';

        try {
            const response = await $.ajax({
                url: API_ENDPOINT,
                type: 'POST',
                data: params
            });

            this.ui.hideLoading();

            if (response.error) {
                this.ui.showError('Chart Error: ' + response.error);
                return;
            }

            // Render the chart
            await this.renderChart(response.graph);

            // Return response for additional processing if needed
            return response;

        } catch (error) {
            this.ui.hideLoading();
            this.ui.showError('Chart request failed. Please try again.');
            throw error;
        }
    }

    async renderChart(graphData) {
        const figData = JSON.parse(graphData);

        // Detect dark mode
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;

        // Apply design improvements for clarity, hierarchy, color, contrast, typography
        // Typography: Sans-serif font, consistent sizes
        figData.layout.font = {
            family: 'Arial, sans-serif',
            size: 12,
            color: isDarkMode ? '#f3f4f6' : '#333333'
        };

        // Color and Contrast: Neutral palette, high contrast
        figData.layout.plot_bgcolor = isDarkMode ? '#1f2937' : 'white';
        figData.layout.paper_bgcolor = isDarkMode ? '#111827' : 'white';

        // Margins for breathing space (simplicity)
        figData.layout.margin = { l: 40, r: 40, t: 40, b: 40 };

        // Visual Hierarchy: No grids for cleaner look
        const gridColor = isDarkMode ? '#374151' : 'rgba(0,0,0,0.05)';
        figData.layout.xaxis = {
            ...figData.layout.xaxis || {},
            showgrid: false,
            zeroline: false,
            title: {
                ...figData.layout.xaxis.title || {},
                font: { size: 14 }
            }
        };
        figData.layout.yaxis = {
            ...figData.layout.yaxis || {},
            showgrid: false,
            zeroline: false,
            title: {
                ...figData.layout.yaxis.title || {},
                font: { size: 14 }
            }
        };

        // Apply to all subplots yaxes
        for (let i = 2; i <= 4; i++) {
            const yKey = `yaxis${i}`;
            if (figData.layout[yKey]) {
                figData.layout[yKey].showgrid = false;
                figData.layout[yKey].zeroline = false;
            }
        }

        // Apply mode-specific layout adjustments
        if (this.mode === 'detailed') {
            figData.layout.height = Math.max(600, window.innerHeight * 0.75);
        }

        // Enhance traces for stock-specific styling (e.g., candlestick colors)
        figData.data.forEach(trace => {
            if (trace.type === 'candlestick') {
                trace.increasing = {
                    fillcolor: '#22c55e', // Green for up
                    line: { color: '#22c55e' }
                };
                trace.decreasing = {
                    fillcolor: '#ef4444', // Red for down
                    line: { color: '#ef4444' }
                };
            } else if (trace.type === 'bar' && trace.name?.toLowerCase().includes('volume')) {
                trace.opacity = 0.5;
            }
            // Limit to essential series; assume backend handles <5 series
        });

        // Interactivity: Responsive, no modebar for simplicity, enable zoom/pan
        const config = {
            responsive: true,
            displayModeBar: false,
            scrollZoom: true,
            modeBarButtonsToRemove: ['toImage', 'sendDataToCloud']
        };

        await Plotly.newPlot(this.containerId, figData.data, figData.layout, config);

        // Setup click handler
        const graphDiv = document.getElementById(this.containerId);
        graphDiv.on('plotly_click', (data) => this.handleChartClick(data));

        // Store chart data for trendlines
        if (figData.data.length > 0) {
            this.state.chartDataX = figData.data[0].x || [];
        }

        // Restore persistent trendlines after chart refresh
        this.state.restoreTrendlines(this.containerId);

        // Update indicator visual state after chart rendering
        this.ui.updateIndicatorVisualState();

        console.log(`✅ Chart rendered in ${this.mode} mode`);
    }

    // ========================================
    // CHART INTERACTION HANDLERS
    // ========================================

    handleChartClick(data) {
        const clickMode = this.getChartClickMode();
        const handler = this.modes[clickMode];
        if (handler) {
            handler.handleClick(data);
        }
    }

    handleFibonacciClick(clickedY) {
        if ($('#manualFibMode').is(':checked')) {
            console.log('📊 Manual Fib: Setting high value to', clickedY.toFixed(2));
            $('#fibHighValue').val(clickedY.toFixed(2));

            // Provide visual feedback
            const input = $('#fibHighValue');
            input.addClass('highlight-input');
            setTimeout(() => input.removeClass('highlight-input'), 1000);

            this.loadChartData(true); // Refresh chart only
        }
    }

    handleTrendlineClick(data) {
        const mode = $('#trendLineMode').val();
        if (mode === 'off') return;

        const clickedX = data.points[0].x;
        const clickedY = data.points[0].y;

        if (mode === 'horizontal') {
            this.addHorizontalTrendline(clickedY);
        } else if (mode === 'point') {
            this.addPointToPointTrendline(clickedX, clickedY);
        }
    }

    addHorizontalTrendline(clickedY) {
        this.state.trendLineCount++;

        if (!this.state.chartDataX || this.state.chartDataX.length < 2) return;

        const xStart = this.state.chartDataX[0];
        const xEnd = this.state.chartDataX[this.state.chartDataX.length - 1];
        const color = this.randomColor();

        const trendLine = {
            type: 'horizontal',
            id: 'H-Line-' + this.state.trendLineCount,
            x: [xStart, xEnd],
            y: [clickedY, clickedY],
            color: color,
            trace: {
                x: [xStart, xEnd],
                y: [clickedY, clickedY],
                mode: 'lines',
                line: {
                    color: color,
                    width: 2,
                    dash: 'dot'
                },
                name: 'H-Line ' + this.state.trendLineCount,
                hoverinfo: 'none'
            }
        };

        // Store persistently
        this.state.trendLines.push(trendLine);

        // Add to chart
        Plotly.addTraces(this.containerId, trendLine.trace);

        console.log('📈 Added horizontal trendline at', clickedY.toFixed(2));
    }

    addPointToPointTrendline(clickedX, clickedY) {
        if (!this.state.pointForLine) {
            this.state.pointForLine = { x: clickedX, y: clickedY };
            console.log('📈 First point selected for trendline');
        } else {
            this.state.trendLineCount++;
            const color = this.randomColor();

            const trendLine = {
                type: 'point-to-point',
                id: 'P2P-Line-' + this.state.trendLineCount,
                x: [this.state.pointForLine.x, clickedX],
                y: [this.state.pointForLine.y, clickedY],
                color: color,
                trace: {
                    x: [this.state.pointForLine.x, clickedX],
                    y: [this.state.pointForLine.y, clickedY],
                    mode: 'lines',
                    line: {
                        color: color,
                        width: 2
                    },
                    name: 'Line ' + this.state.trendLineCount,
                    hoverinfo: 'none'
                }
            };

            // Store persistently
            this.state.trendLines.push(trendLine);

            // Add to chart
            Plotly.addTraces(this.containerId, trendLine.trace);

            console.log('📈 Added point-to-point trendline');
            this.state.pointForLine = null;
        }
    }

    // ========================================
    // EVENT LISTENERS SETUP
    // ========================================

    setupEventListeners() {
        this.setupModeListeners();
        this.setupFibListeners();
        this.setupMAListeners();
        this.setupElliottListeners();
        this.setupIndicatorListeners();
        this.setupSettingsListeners();
        this.setupNavigationListeners();
    }

    setupModeListeners() {
        $('input[name="analysisMode"]').on('change', () => {
            const analysisMode = this.getAnalysisMode();
            this.ui.updateSettingsVisibility(analysisMode);
            this.handleModeChange(analysisMode);
        });
    }

    setupFibListeners() {
        $('#manualFibMode').on('change', () => {
            if (!$('#manualFibMode').is(':checked')) {
                $('#fibHighValue').val('');
            }
            this.loadChartData(true);
        });

        $('#showExtensions, #showFib').on('change', () => {
            this.loadChartData(true);
        });

        $('#fibHighValue').on('change', () => {
            if ($('#fibHighValue').val()) {
                this.loadChartData(true);
            }
        });
    }

    setupMAListeners() {
        $('.ma-checkbox').change(() => {
            this.loadChartData(true);
        });

        // Custom MA management
        $('#add-custom-ma').click(() => {
            const period = parseInt($('#custom-ma-input').val());
            if (this.state.addCustomMovingAverage(period)) {
                $('#custom-ma-input').val('');
                this.ui.updateCustomMADisplay(this.state.customMAs);
                this.loadChartData(true);
            }
        });

        $('#custom-ma-input').keypress((e) => {
            if (e.which === 13) {
                $('#add-custom-ma').click();
            }
        });

        // Remove custom MA
        $(document).on('click', '.remove-custom-ma', (e) => {
            const period = parseInt($(e.currentTarget).data('period'));
            if (this.state.removeCustomMovingAverage(period)) {
                this.ui.updateCustomMADisplay(this.state.customMAs);
                this.loadChartData(true);
            }
        });

        // MA presets
        $('#ma-preset-none').click(() => {
            $('.ma-checkbox').prop('checked', false);
            this.loadChartData(true);
        });

        $('#ma-preset-basic').click(() => {
            $('.ma-checkbox').prop('checked', false);
            $('#ma-20, #ma-50').prop('checked', true);
            this.loadChartData(true);
        });

        $('#ma-preset-extended').click(() => {
            $('.ma-checkbox').prop('checked', false);
            $('#ma-20, #ma-50, #ma-200').prop('checked', true);
            this.loadChartData(true);
        });

        $('#ma-preset-day-trading').click(() => {
            $('.ma-checkbox').prop('checked', false);
            $('#ma-5, #ma-10, #ma-20').prop('checked', true);
            this.loadChartData(true);
        });
    }

    setupElliottListeners() {
        // Remove Elliott point
        $(document).on('click', '.remove-point', (e) => {
            const index = parseInt($(e.currentTarget).data('index'));
            this.state.elliottPoints.splice(index, 1);
            this.ui.updateElliottDisplay(this.state.elliottPoints);
            this.loadChartData(true);
        });

        $('#clear-elliott-points').click(() => {
            this.state.elliottPoints = [];
            this.ui.updateElliottDisplay(this.state.elliottPoints);
            this.loadChartData(true);
        });

        // Elliott wave enhancements
        $('#show-elliott-fib-levels, #extend-elliott-projections').on('change', () => {
            this.loadChartData(true);
        });

        // Elliott wave auto-generation toggle
        $('#show-elliott-auto-waves').on('change', () => {
            this.loadChartData(true);
        });
    }

    setupIndicatorListeners() {
        $('#showRSI, #showMACD, #showVolume, #showCandlestick').on('change', () => {
            this.ui.updateIndicatorVisualState();
            this.loadChartData(true);
        });
    }

    setupSettingsListeners() {
        $(document).on('click', '#chart-settings-toggle', () => {
            this.ui.toggleSettings();
        });
    }

    setupNavigationListeners() {
        $('#detailed-graph-btn').click(() => {
            this.navigateToDetailed();
        });

        $('#back-to-dashboard-btn').click(() => {
            this.navigateToDashboard();
        });
    }

    handleModeChange(analysisMode) {
        // Handle mode-specific logic - RSI, MACD, Volume, and Candlestick work as independent toggles
        if (analysisMode === 'rsi') {
            // Toggle RSI indicator when RSI mode is selected (don't affect others)
            const currentRSI = $('#showRSI').is(':checked');
            $('#showRSI').prop('checked', !currentRSI);
        } else if (analysisMode === 'macd') {
            // Toggle MACD indicator when MACD mode is selected (don't affect others)
            const currentMACD = $('#showMACD').is(':checked');
            $('#showMACD').prop('checked', !currentMACD);
        } else if (analysisMode === 'volume') {
            // Toggle Volume indicator when Volume mode is selected
            const currentVolume = $('#showVolume').is(':checked');
            $('#showVolume').prop('checked', !currentVolume);
        } else if (analysisMode === 'candlestick') {
            // Toggle Candlestick indicator when Candlestick mode is selected
            const currentCandlestick = $('#showCandlestick').is(':checked');
            $('#showCandlestick').prop('checked', !currentCandlestick);
        }
        // For other modes (fib, trendlines, elliott, ma), don't change indicator settings
        // This allows all indicators to persist across all modes

        // Update visual indicator state after changing checkboxes
        this.ui.updateIndicatorVisualState();

        // Refresh chart with new mode settings
        this.loadChartData(true);
    }

    // ========================================
    // NAVIGATION METHODS (to be overridden)
    // ========================================

    navigateToDetailed() {
        // This will be overridden by the parent application
        const ticker = $('#ticker').val().trim();
        if (ticker) {
            window.location.href = `/detailed-graph/${ticker}`;
        }
    }

    navigateToDashboard() {
        // This will be overridden by the parent application
        window.location.href = '/';
    }

    // ========================================
    // PUBLIC API METHODS
    // ========================================

    async updateChart(ticker, period) {
        $('#ticker').val(ticker);
        $(`input[name="period"][value="${period}"]`).prop('checked', true);
        return await this.loadChartData();
    }

    setChartMode(mode) {
        $(`input[name="analysisMode"][value="${mode}"]`).prop('checked', true).trigger('change');
    }

    getChartState() {
        return {
            ticker: $('#ticker').val().trim(),
            period: $('input[name="period"]:checked').val(),
            chartMode: this.getChartClickMode(),
            movingAverages: this.getSelectedMovingAverages(),
            customMAs: [...this.state.customMAs],
            elliottPoints: [...this.state.elliottPoints],
            fibSettings: {
                manualMode: $('#manualFibMode').is(':checked'),
                fibHigh: $('#fibHighValue').val(),
                showExtensions: $('#showExtensions').is(':checked'),
                showFib: $('#showFib').is(':checked')
            }
        };
    }

    restoreChartState(state) {
        if (state.ticker) $('#ticker').val(state.ticker);
        if (state.period) $(`input[name="period"][value="${state.period}"]`).prop('checked', true);
        if (state.chartMode) this.setChartMode(state.chartMode);

        if (state.customMAs) {
            this.state.customMAs = [...state.customMAs];
            this.ui.updateCustomMADisplay(this.state.customMAs);
        }

        if (state.elliottPoints) {
            this.state.elliottPoints = [...state.elliottPoints];
            this.ui.updateElliottDisplay(this.state.elliottPoints);
        }

        if (state.fibSettings) {
            $('#manualFibMode').prop('checked', state.fibSettings.manualMode);
            $('#fibHighValue').val(state.fibSettings.fibHigh || '');
            $('#showExtensions').prop('checked', state.fibSettings.showExtensions);
            $('#showFib').prop('checked', state.fibSettings.showFib);
        }
    }
}

// Export for use in other modules
window.StockChart = StockChart;