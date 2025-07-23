/**
 * Stock Chart Module
 * Handles all chart-related functionality including Plotly integration,
 * technical analysis tools, and chart interactions
 */

console.log("✅ chart.js loaded");

class StockChart {
    constructor(containerId, mode = 'compact') {
        this.containerId = containerId;
        this.mode = mode; // 'compact' or 'detailed'
        this.chartDataX = [];
        this.pointForLine = null;
        this.trendLineCount = 0;
        this.customMAs = [];
        this.elliottPoints = [];
        this.trendLines = []; // Store persistent trendlines

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
        if (analysisMode === 'rsi' || analysisMode === 'macd' || analysisMode === 'ma') {
            return 'fib'; // Default click mode for indicator modes
        }
        return analysisMode;
    }

    getAnalysisMode() {
        return $('input[name="analysisMode"]:checked').val();
    }

    randomColor() {
        const colors = ['#FF5733', '#33FFCC', '#FF33A6', '#3371FF', '#FFD633', '#4CAF50'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    getSelectedMovingAverages() {
        const selectedMAs = [];

        // Get checked standard MAs
        $('.ma-checkbox:checked').each(function () {
            selectedMAs.push(parseInt($(this).val()));
        });

        // Add custom MAs
        this.customMAs.forEach(function (period) {
            selectedMAs.push(period);
        });

        // Remove duplicates and sort
        return [...new Set(selectedMAs)].sort((a, b) => a - b);
    }

    updateElliottDisplay() {
        const grid = $('#elliott-points-grid');
        const countSpan = $('#elliott-points-count');
        
        console.log('Updating Elliott display with points:', this.elliottPoints);
        
        // Update points count
        countSpan.text(this.elliottPoints.length);
        
        // Update points grid
        grid.empty();
        this.elliottPoints.forEach((p, i) => {
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

        console.log(`📊 Indicator states updated - RSI: ${rsiEnabled}, MACD: ${macdEnabled}`);
    }

    // ========================================
    // CHART DATA AND RENDERING
    // ========================================

    getCommonFetchParams() {
        const ticker = $('#ticker').val().trim();
        const period = $('input[name="period"]:checked').val();
        const chartMode = this.getChartClickMode();
        // Fibonacci settings - Always send if configured (persist across modes)
        const manualFib = $('#manualFibMode').is(':checked');
        const showExtensions = $('#showExtensions').is(':checked');
        const fibHigh = $('#fibHighValue').val();
        const showFib = $('#showFib').is(':checked');
        
        // Moving Averages - Always send if configured (persist across modes)
        const selectedMAs = this.getSelectedMovingAverages();
        const movingAveragesParam = selectedMAs.length > 0 ? selectedMAs.join(',') : '';

        // Elliott Wave Support - Always send points if they exist (persist across modes)
        const elliottPointsParam = (this.elliottPoints.length > 0) ?
            JSON.stringify(this.elliottPoints) : '';

        // Elliott Wave Auto-generation toggle
        const showElliottAutoWaves = $('#show-elliott-auto-waves').is(':checked');

        // NEW: Technical Indicators
        const showRSI = $('#showRSI').is(':checked');
        const showMACD = $('#showMACD').is(':checked');

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
            showMACD: showMACD
        };
    }

    async loadChartData(onlyChart = false) {
        const params = this.getCommonFetchParams();

        if (!params.ticker) {
            this.showError('Please enter a valid ticker symbol');
            return Promise.reject('Invalid ticker');
        }

        this.showLoading();
        this.hideError();

        params.includeFinancials = onlyChart ? 'false' : 'true';

        try {
            const response = await $.ajax({
                url: '/plot',
                type: 'POST',
                data: params
            });

            this.hideLoading();

            if (response.error) {
                this.showError('Chart Error: ' + response.error);
                return;
            }

            // Render the chart
            await this.renderChart(response.graph);

            // Return response for additional processing if needed
            return response;

        } catch (error) {
            this.hideLoading();
            this.showError('Chart request failed. Please try again.');
            throw error;
        }
    }

    async renderChart(graphData) {
        const figData = JSON.parse(graphData);

        // Apply mode-specific layout adjustments
        if (this.mode === 'detailed') {
            figData.layout.height = Math.max(600, window.innerHeight * 0.75);
            figData.layout.margin = { l: 60, r: 60, t: 60, b: 60 };
        }

        await Plotly.newPlot(this.containerId, figData.data, figData.layout);

        // Setup click handler
        const graphDiv = document.getElementById(this.containerId);
        graphDiv.on('plotly_click', (data) => this.handleChartClick(data));

        // Store chart data for trendlines
        if (figData.data.length > 0) {
            this.chartDataX = figData.data[0].x || [];
        }

        // Restore persistent trendlines after chart refresh
        this.restoreTrendlines();

        // Update indicator visual state after chart rendering
        this.updateIndicatorVisualState();

        console.log(`✅ Chart rendered in ${this.mode} mode`);
    }

    // ========================================
    // TRENDLINE PERSISTENCE
    // ========================================

    restoreTrendlines() {
        // Re-add all stored trendlines to the chart
        this.trendLines.forEach(trendLine => {
            try {
                Plotly.addTraces(this.containerId, trendLine.trace);
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
        this.loadChartData(true); // Refresh chart to remove trendlines
    }

    // ========================================
    // CHART INTERACTION HANDLERS
    // ========================================

    handleChartClick(data) {
        const clickMode = this.getChartClickMode();
        const clickedY = data.points[0].y;

        if (clickMode === 'fib') {
            this.handleFibonacciClick(clickedY);
        } else if (clickMode === 'trendlines') {
            this.handleTrendlineClick(data);
        } else if (clickMode === 'elliott') {
            this.handleElliottClick(data);
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

    handleElliottClick(data) {
        const clickedX = data.points[0].x;
        const clickedY = data.points[0].y.toFixed(2);

        this.elliottPoints.push({ x: clickedX, y: clickedY });
        this.updateElliottDisplay();
        this.loadChartData(true); // Refresh chart to show Elliott wave updates
    }

    addHorizontalTrendline(clickedY) {
        this.trendLineCount++;

        if (!this.chartDataX || this.chartDataX.length < 2) return;

        const xStart = this.chartDataX[0];
        const xEnd = this.chartDataX[this.chartDataX.length - 1];
        const color = this.randomColor();

        const trendLine = {
            type: 'horizontal',
            id: 'H-Line-' + this.trendLineCount,
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
                name: 'H-Line ' + this.trendLineCount,
                hoverinfo: 'none'
            }
        };

        // Store persistently
        this.trendLines.push(trendLine);

        // Add to chart
        Plotly.addTraces(this.containerId, trendLine.trace);
        
        console.log('📈 Added horizontal trendline at', clickedY.toFixed(2));
    }

    addPointToPointTrendline(clickedX, clickedY) {
        if (!this.pointForLine) {
            this.pointForLine = { x: clickedX, y: clickedY };
            console.log('📈 First point selected for trendline');
        } else {
            this.trendLineCount++;
            const color = this.randomColor();

            const trendLine = {
                type: 'point-to-point',
                id: 'P2P-Line-' + this.trendLineCount,
                x: [this.pointForLine.x, clickedX],
                y: [this.pointForLine.y, clickedY],
                color: color,
                trace: {
                    x: [this.pointForLine.x, clickedX],
                    y: [this.pointForLine.y, clickedY],
                    mode: 'lines',
                    line: {
                        color: color,
                        width: 2
                    },
                    name: 'Line ' + this.trendLineCount,
                    hoverinfo: 'none'
                }
            };

            // Store persistently
            this.trendLines.push(trendLine);

            // Add to chart
            Plotly.addTraces(this.containerId, trendLine.trace);
            
            console.log('📈 Added point-to-point trendline');
            this.pointForLine = null;
        }
    }

    // ========================================
    // MOVING AVERAGES MANAGEMENT
    // ========================================

    addCustomMovingAverage(period) {
        if (period && period > 0 && period <= 500) {
            if (!this.customMAs.includes(period)) {
                this.customMAs.push(period);
                this.updateCustomMADisplay();
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
            this.updateCustomMADisplay();
            return true;
        }
        return false;
    }

    updateCustomMADisplay() {
        const customMAList = $('#custom-ma-display');
        customMAList.empty();

        if (this.customMAs.length === 0) {
            customMAList.hide();
            return;
        }

        customMAList.show();

        this.customMAs.forEach((period) => {
            const tag = $(`
                <span class="custom-ma-tag">
                    MA${period}
                    <span class="remove-custom-ma" data-period="${period}">×</span>
                </span>
            `);
            customMAList.append(tag);
        });
    }

    // ========================================
    // UI STATE MANAGEMENT
    // ========================================

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

    toggleSettings() {
        const settings = $('#chart-settings');
        const button = $('#chart-settings-toggle');
        
        settings.slideToggle(300, function() {
            // Update button text after animation completes
            if (settings.is(':visible')) {
                button.text('Hide Settings');
            } else {
                button.text('Settings');
            }
        });
        
        console.log('Settings toggled, visible:', settings.is(':visible'));
    }

    // ========================================
    // EVENT LISTENERS SETUP
    // ========================================

    setupEventListeners() {
        const self = this;

        // Analysis mode change
        $('input[name="analysisMode"]').on('change', function () {
            const analysisMode = self.getAnalysisMode();
            self.updateSettingsVisibility(analysisMode);
            self.handleModeChange(analysisMode);
        });

        // Fibonacci settings - Always refresh chart (persist across modes)
        $('#manualFibMode').on('change', function () {
            if (!$(this).is(':checked')) {
                $('#fibHighValue').val('');
            }
            self.loadChartData(true);
        });

        $('#showExtensions, #showFib').on('change', function () {
            self.loadChartData(true);
        });

        $('#fibHighValue').on('change', function () {
            if ($(this).val()) {
                self.loadChartData(true);
            }
        });

        // Moving averages - Always refresh chart (persist across modes)
        $('.ma-checkbox').change(function () {
            self.loadChartData(true);
        });

        // Custom MA management
        $('#add-custom-ma').click(function () {
            const period = parseInt($('#custom-ma-input').val());
            if (self.addCustomMovingAverage(period)) {
                $('#custom-ma-input').val('');
                self.loadChartData(true);
            }
        });

        $('#custom-ma-input').keypress(function (e) {
            if (e.which === 13) {
                $('#add-custom-ma').click();
            }
        });

        // Remove custom MA
        $(document).on('click', '.remove-custom-ma', function () {
            const period = parseInt($(this).data('period'));
            if (self.removeCustomMovingAverage(period)) {
                self.loadChartData(true);
            }
        });

        // Elliott wave management
        $(document).on('click', '.remove-point', function () {
            const index = parseInt($(this).data('index'));
            self.elliottPoints.splice(index, 1);
            self.updateElliottDisplay();
            self.loadChartData(true);
        });

        $('#clear-elliott-points').click(function () {
            self.elliottPoints = [];
            self.updateElliottDisplay();
            self.loadChartData(true);
        });

        // MA presets - Always refresh chart (persist across modes)
        $('#ma-preset-none').click(function () {
            $('.ma-checkbox').prop('checked', false);
            self.loadChartData(true);
        });

        $('#ma-preset-basic').click(function () {
            $('.ma-checkbox').prop('checked', false);
            $('#ma-20, #ma-50').prop('checked', true);
            self.loadChartData(true);
        });

        $('#ma-preset-extended').click(function () {
            $('.ma-checkbox').prop('checked', false);
            $('#ma-20, #ma-50, #ma-200').prop('checked', true);
            self.loadChartData(true);
        });

        $('#ma-preset-day-trading').click(function () {
            $('.ma-checkbox').prop('checked', false);
            $('#ma-5, #ma-10, #ma-20').prop('checked', true);
            self.loadChartData(true);
        });

        // Technical indicators toggles
        $('#showRSI, #showMACD').on('change', function () {
            self.updateIndicatorVisualState();
            self.loadChartData(true);
        });

        // Elliott wave enhancements
        $('#show-elliott-fib-levels, #extend-elliott-projections').on('change', function () {
            self.loadChartData(true);
        });

        // Elliott wave auto-generation toggle
        $('#show-elliott-auto-waves').on('change', function () {
            self.loadChartData(true);
        });

        // Chart settings toggle
        $(document).on('click', '#chart-settings-toggle', function () {
            self.toggleSettings();
        });

        // Navigation buttons (will be handled by parent application)
        $('#detailed-graph-btn').click(function () {
            self.navigateToDetailed();
        });

        $('#back-to-dashboard-btn').click(function () {
            self.navigateToDashboard();
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
            this.updateElliottDisplay();
        } else if (mode === 'rsi') {
            $('#rsiSettings').addClass('active');
        } else if (mode === 'macd') {
            $('#macdSettings').addClass('active');
        } else if (mode === 'ma') {
            $('#maSettings').addClass('active');
        }
    }

    handleModeChange(analysisMode) {
        // Handle mode-specific logic - RSI and MACD now work as independent toggles
        if (analysisMode === 'rsi') {
            // Toggle RSI indicator when RSI mode is selected (don't affect MACD)
            const currentRSI = $('#showRSI').is(':checked');
            $('#showRSI').prop('checked', !currentRSI);
        } else if (analysisMode === 'macd') {
            // Toggle MACD indicator when MACD mode is selected (don't affect RSI)
            const currentMACD = $('#showMACD').is(':checked');
            $('#showMACD').prop('checked', !currentMACD);
        }
        // For other modes (fib, trendlines, elliott, ma), don't change indicator settings
        // This allows RSI and MACD to persist across all modes
        
        // Update visual indicator state after changing checkboxes
        this.updateIndicatorVisualState();
        
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
        $(`input[name="chartClickMode"][value="${mode}"]`).prop('checked', true).trigger('change');
    }

    getChartState() {
        return {
            ticker: $('#ticker').val().trim(),
            period: $('input[name="period"]:checked').val(),
            chartMode: this.getChartClickMode(),
            movingAverages: this.getSelectedMovingAverages(),
            customMAs: [...this.customMAs],
            elliottPoints: [...this.elliottPoints],
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
            this.customMAs = [...state.customMAs];
            this.updateCustomMADisplay();
        }

        if (state.elliottPoints) {
            this.elliottPoints = [...state.elliottPoints];
            this.updateElliottDisplay();
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