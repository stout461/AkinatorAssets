console.log("✅ chart.js loaded");

// Constants (extracted for easy tweaking)
const DEFAULT_COLORS = ['#FF5733', '#33FFCC', '#FF33A6', '#3371FF', '#FFD633', '#4CAF50'];
const API_ENDPOINT = '/plot';

// Note: SettingsCoordinator is loaded from settings-coordinator.js

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
        
        // Update coordinated settings
        this.chart.settingsCoordinator.updateSetting('elliottWave', 'points', [...this.chart.state.elliottPoints]);
    }
}

// Sub-class: UI Manager
class ChartUI {
    constructor(chart) {
        this.chart = chart;
        this.containerId = chart.containerId;
    }

    showLoading(message = 'Loading...') {
        $(`#${this.containerId}-loading, #chart-loading`).show();
        // Update loading message if provided
        $(`#${this.containerId}-loading .loading-message, #chart-loading .loading-message`).text(message);
    }

    hideLoading() {
        $(`#${this.containerId}-loading, #chart-loading`).hide();
    }

    showError(message, type = 'error', options = {}) {
        const errorElement = $(`#${this.containerId}-error, #chart-error`);
        
        // Clear any existing error classes
        errorElement.removeClass('alert-danger alert-warning alert-info alert-success');
        
        // Add appropriate class based on error type
        switch (type) {
            case 'warning':
                errorElement.addClass('alert-warning');
                break;
            case 'info':
                errorElement.addClass('alert-info');
                break;
            case 'success':
                errorElement.addClass('alert-success');
                break;
            default:
                errorElement.addClass('alert-danger');
        }
        
        errorElement.text(message).show();
        
        // Auto-hide after specified duration
        if (options.autoHide && options.duration) {
            setTimeout(() => {
                this.hideError();
            }, options.duration);
        }
    }

    hideError() {
        $(`#${this.containerId}-error, #chart-error`).hide();
    }

    /**
     * Show loading state with progress indicator for complex operations
     */
    showProgressLoading(message, progress = 0) {
        const loadingElement = $(`#${this.containerId}-loading, #chart-loading`);
        
        // Create or update progress bar
        let progressBar = loadingElement.find('.progress-bar');
        if (progressBar.length === 0) {
            loadingElement.append(`
                <div class="progress mt-2" style="height: 4px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: 0%"></div>
                </div>
            `);
            progressBar = loadingElement.find('.progress-bar');
        }
        
        // Update progress
        progressBar.css('width', `${progress}%`);
        
        // Update message
        loadingElement.find('.loading-message').text(message);
        loadingElement.show();
    }

    /**
     * Show conflict resolution dialog with suggested alternatives
     */
    showConflictDialog(conflicts, alternatives = [], onResolve = null) {
        // Create modal dialog HTML
        const modalId = `conflict-modal-${this.containerId}`;
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                                Configuration Conflicts Detected
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning">
                                <strong>The following conflicts were detected:</strong>
                                <ul class="mt-2 mb-0">
                                    ${conflicts.map(conflict => `<li>${conflict.message}</li>`).join('')}
                                </ul>
                            </div>
                            
                            ${alternatives.length > 0 ? `
                                <h6>Suggested Solutions:</h6>
                                <div class="list-group">
                                    ${alternatives.map((alt, index) => `
                                        <div class="list-group-item">
                                            <div class="d-flex w-100 justify-content-between">
                                                <h6 class="mb-1">Option ${index + 1}</h6>
                                                <button class="btn btn-sm btn-outline-primary apply-alternative" 
                                                        data-index="${index}">Apply</button>
                                            </div>
                                            <p class="mb-1">${alt.description}</p>
                                            <small class="text-muted">
                                                Subplots: ${alt.subplots.join(', ') || 'None'}
                                            </small>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Keep Current Settings
                            </button>
                            ${alternatives.length > 0 ? `
                                <button type="button" class="btn btn-primary" id="apply-first-alternative">
                                    Apply Recommended Solution
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        $(`#${modalId}`).remove();
        
        // Add modal to DOM
        $('body').append(modalHtml);
        
        // Set up event handlers
        const modal = $(`#${modalId}`);
        
        // Handle alternative application
        modal.find('.apply-alternative').on('click', (e) => {
            const index = parseInt($(e.target).data('index'));
            const alternative = alternatives[index];
            if (onResolve) {
                onResolve(alternative);
            }
            modal.modal('hide');
        });
        
        // Handle recommended solution
        modal.find('#apply-first-alternative').on('click', () => {
            if (alternatives.length > 0 && onResolve) {
                onResolve(alternatives[0]);
            }
            modal.modal('hide');
        });
        
        // Clean up modal after hiding
        modal.on('hidden.bs.modal', () => {
            modal.remove();
        });
        
        // Show modal
        modal.modal('show');
    }

    /**
     * Show validation feedback for invalid configurations
     */
    showValidationFeedback(field, message, type = 'error') {
        const fieldElement = $(`#${field}`);
        const feedbackId = `${field}-feedback`;
        
        // Remove existing feedback
        $(`#${feedbackId}`).remove();
        fieldElement.removeClass('is-invalid is-valid');
        
        // Add new feedback
        const feedbackClass = type === 'error' ? 'invalid-feedback' : 'valid-feedback';
        const inputClass = type === 'error' ? 'is-invalid' : 'is-valid';
        
        fieldElement.addClass(inputClass);
        fieldElement.after(`
            <div id="${feedbackId}" class="${feedbackClass}">
                ${message}
            </div>
        `);
        
        // Auto-clear after 5 seconds for non-error feedback
        if (type !== 'error') {
            setTimeout(() => {
                this.clearValidationFeedback(field);
            }, 5000);
        }
    }

    /**
     * Clear validation feedback for a field
     */
    clearValidationFeedback(field) {
        const fieldElement = $(`#${field}`);
        const feedbackId = `${field}-feedback`;
        
        $(`#${feedbackId}`).remove();
        fieldElement.removeClass('is-invalid is-valid');
    }

    /**
     * Show toast notification for quick feedback
     */
    showToast(message, type = 'info', duration = 3000) {
        const toastId = `toast-${Date.now()}`;
        const toastClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${toastClass} border-0" 
                 role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        if ($('#toast-container').length === 0) {
            $('body').append(`
                <div id="toast-container" class="toast-container position-fixed top-0 end-0 p-3" 
                     style="z-index: 1055;"></div>
            `);
        }
        
        // Add toast
        $('#toast-container').append(toastHtml);
        
        // Show toast
        const toastElement = $(`#${toastId}`);
        const toast = new bootstrap.Toast(toastElement[0], { delay: duration });
        toast.show();
        
        // Clean up after hiding
        toastElement.on('hidden.bs.toast', () => {
            toastElement.remove();
        });
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

        console.log(`📊 Indicator states updated - RSI: ${rsiEnabled}, MACD: ${macdEnabled}, Volume: ${volumeEnabled}`);
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
        
        // Initialize SettingsCoordinator for unified settings management
        this.settingsCoordinator = new SettingsCoordinator(this);
        
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
        this.setupSettingsCoordination();
        this.initializeGraphSettings();
        console.log(`📊 StockChart initialized in ${this.mode} mode for container: ${this.containerId}`);
    }

    setupSettingsCoordination() {
        // Set up event listeners for coordinated settings management
        this.settingsCoordinator.addEventListener('settingChanged', (data) => {
            this.handleCoordinatedSettingChange(data);
        });

        this.settingsCoordinator.addEventListener('multipleSettingsChanged', (data) => {
            this.handleMultipleSettingsChange(data);
        });

        this.settingsCoordinator.addEventListener('validationError', (data) => {
            this.handleSettingsValidationError(data);
        });

        this.settingsCoordinator.addEventListener('conflictError', (data) => {
            this.handleSettingsConflictError(data);
        });

        // Sync initial settings with DOM
        this.settingsCoordinator.syncWithDOM();
        
        console.log('📊 Settings coordination configured');
    }

    handleCoordinatedSettingChange(data) {
        const { category, key, newValue, oldValue } = data;
        
        // Update DOM elements if needed
        this.syncSettingToDOM(category, key, newValue);
        
        // Update visual indicators
        if (category === 'subplots') {
            this.ui.updateIndicatorVisualState();
        }
        
        // Refresh chart if setting affects visualization
        if (this.shouldRefreshChart(category, key)) {
            this.loadChartData(true);
        }
        
        console.log(`📊 Coordinated setting change: ${category}.${key} = ${newValue}`);
    }

    handleMultipleSettingsChange(data) {
        // Handle multiple settings changes efficiently
        this.settingsCoordinator.syncWithDOM();
        this.ui.updateIndicatorVisualState();
        this.loadChartData(true);
        
        console.log('📊 Multiple coordinated settings changed');
    }

    handleSettingsValidationError(data) {
        console.warn('Settings validation error:', data);
        // Error message is already shown by SettingsCoordinator
    }

    handleSettingsConflictError(data) {
        console.warn('Settings conflict error:', data);
        // Error message is already shown by SettingsCoordinator
    }

    syncSettingToDOM(category, key, value) {
        // Sync specific setting changes back to DOM elements
        if (category === 'subplots') {
            $(`#${key}`).prop('checked', value);
        } else if (category === 'graphSettings') {
            const domId = this.mapSettingToDOMId(key);
            if (domId) {
                $(`#${domId}`).prop('checked', value);
            }
        } else if (category === 'analysisMode') {
            $(`input[name="analysisMode"][value="${value}"]`).prop('checked', true);
        }
    }

    mapSettingToDOMId(settingKey) {
        const mapping = {
            'showCandlestick': 'showCandlestick',
            'showGraphLines': 'showGraphLines',
            'showTimeSelector': 'showTimeSelector'
        };
        return mapping[settingKey];
    }

    shouldRefreshChart(category, key) {
        // Determine if a setting change requires chart refresh
        const refreshTriggers = [
            'subplots',
            'graphSettings',
            'fibonacciSettings',
            'movingAverages',
            'elliottWave'
        ];
        return refreshTriggers.includes(category);
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
        
        // Get unified subplot configuration from SettingsCoordinator
        const subplotConfig = this.settingsCoordinator.generateUnifiedSubplotConfig();
        
        // Fibonacci settings - Always send if configured (persist across modes)
        const fibSettings = this.settingsCoordinator.getSetting('fibonacciSettings');
        const manualFib = $('#manualFibMode').is(':checked');
        const showExtensions = $('#showExtensions').is(':checked');
        const fibHigh = $('#fibHighValue').val();
        const showFib = $('#showFib').is(':checked');

        // Moving Averages - Always send if configured (persist across modes)
        const selectedMAs = this.getSelectedMovingAverages();
        const movingAveragesParam = selectedMAs.length > 0 ? selectedMAs.join(',') : '';

        // Elliott Wave Support - Always send points if they exist (persist across modes)
        const elliottPointsParam = (this.state.elliottPoints.length > 0) ?
            JSON.stringify(this.state.elliottPoints) : '';

        // Elliott Wave Auto-generation toggle
        const showElliottAutoWaves = $('#show-elliott-auto-waves').is(':checked');

        // Include mode-specific params if any
        const modeHandler = this.modes[chartMode];
        const modeParams = modeHandler ? modeHandler.getParams() : {};

        // Build parameters object with unified subplot configuration
        const params = {
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
            ...modeParams
        };

        // Add unified subplot configuration if subplots are active
        if (subplotConfig.subplots.length > 0 || 
            subplotConfig.graph_settings.show_candlestick || 
            subplotConfig.graph_settings.show_time_selector) {
            params.subplotConfig = JSON.stringify(subplotConfig);
        } else {
            // Fallback to individual flags for backward compatibility
            params.showRSI = this.settingsCoordinator.getSetting('subplots', 'showRSI');
            params.showMACD = this.settingsCoordinator.getSetting('subplots', 'showMACD');
            params.showVolume = this.settingsCoordinator.getSetting('subplots', 'showVolume');
            params.showCandlestick = this.settingsCoordinator.getSetting('graphSettings', 'showCandlestick');
        }

        return params;
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

            // Handle API response conflicts and validation errors
            if (response.error) {
                this.handleAPIError(response);
                return;
            }

            // Handle subplot configuration conflicts from backend
            if (response.conflicts && response.conflicts.length > 0) {
                this.handleBackendConflicts(response);
                return;
            }

            // Update settings from successful API response
            if (response.layoutInfo) {
                this.handleLayoutInfoUpdate(response.layoutInfo);
            }

            // Render the chart
            await this.renderChart(response.graph);

            // Return response for additional processing if needed
            return response;

        } catch (error) {
            this.ui.hideLoading();
            
            // Enhanced error handling for different types of failures
            if (error.status === 400 && error.responseJSON) {
                this.handleValidationError(error.responseJSON);
            } else {
                this.ui.showError('Chart request failed. Please try again.');
            }
            throw error;
        }
    }

    /**
     * Handle API errors with intelligent user feedback
     */
    handleAPIError(response) {
        let errorMessage = response.error;
        
        // Provide more specific error messages based on error type
        if (response.error_type === 'server_error') {
            errorMessage = 'Server error occurred. Please try again in a moment.';
        } else if (response.validation_errors && response.validation_errors.length > 0) {
            errorMessage = response.validation_errors[0].message;
        }
        
        this.ui.showError(errorMessage);
        console.error('API Error:', response);
    }

    /**
     * Handle backend subplot conflicts with user-friendly resolution options
     */
    handleBackendConflicts(response) {
        const conflicts = response.conflicts;
        const suggestions = response.suggestions || [];
        const alternatives = response.alternatives || [];
        
        console.warn('Backend conflicts detected:', conflicts);
        
        // Show conflict resolution dialog if alternatives are available
        if (alternatives.length > 0) {
            this.ui.showConflictDialog(conflicts, alternatives, (selectedAlternative) => {
                console.log('User selected alternative:', selectedAlternative);
                
                // Update settings with the selected alternative configuration
                this.settingsCoordinator.updateFromUnifiedConfig({
                    subplots: selectedAlternative.subplots,
                    graph_settings: this.settingsCoordinator.getSetting('graphSettings')
                });
                
                // Show success feedback
                this.ui.showToast(`Applied: ${selectedAlternative.description}`, 'success', 4000);
                
                // Refresh chart with new configuration
                this.loadChartData(true);
            });
        } else {
            // Fallback to simple error message if no alternatives
            let conflictMessage = 'Subplot configuration conflicts detected. ';
            if (suggestions.length > 0) {
                conflictMessage += suggestions[0];
            }
            this.ui.showError(conflictMessage, 'warning');
        }
    }

    /**
     * Handle validation errors from API with detailed feedback
     */
    handleValidationError(errorResponse) {
        if (errorResponse.conflicts && errorResponse.conflicts.length > 0) {
            this.handleBackendConflicts(errorResponse);
        } else if (errorResponse.validation_errors && errorResponse.validation_errors.length > 0) {
            const firstError = errorResponse.validation_errors[0];
            this.ui.showError(`Validation Error: ${firstError.message}`);
        } else {
            this.ui.showError(errorResponse.error || 'Validation failed');
        }
    }

    /**
     * Handle layout info updates from successful API responses
     */
    handleLayoutInfoUpdate(layoutInfo) {
        // Log layout information for debugging
        console.log('Layout info received:', layoutInfo);
        
        // Show warnings if any conflicts were resolved
        if (layoutInfo.conflictsResolved && layoutInfo.conflictsResolved.length > 0) {
            const resolvedMessage = `Conflicts resolved: ${layoutInfo.conflictsResolved.join(', ')}`;
            console.warn(resolvedMessage);
        }
        
        // Show warnings from backend
        if (layoutInfo.warnings && layoutInfo.warnings.length > 0) {
            layoutInfo.warnings.forEach(warning => {
                console.warn('Backend warning:', warning);
            });
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

        // Apply graph settings after chart is rendered
        this.applyGraphSettings();

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
        $('#manualFibMode').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('fibonacciSettings', 'manualMode', enabled);
            if (!enabled) {
                $('#fibHighValue').val('');
                this.settingsCoordinator.updateSetting('fibonacciSettings', 'fibHigh', '');
            }
        });

        $('#showExtensions').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('fibonacciSettings', 'showExtensions', enabled);
        });

        $('#showFib').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('fibonacciSettings', 'showFib', enabled);
        });

        $('#fibHighValue').on('change', (e) => {
            const value = $(e.target).val();
            this.settingsCoordinator.updateSetting('fibonacciSettings', 'fibHigh', value);
        });
    }

    setupMAListeners() {
        // Standard MA checkboxes - use coordinated settings
        $('.ma-checkbox').change((e) => {
            const selectedMAs = [];
            $('.ma-checkbox:checked').each(function () {
                selectedMAs.push(parseInt($(this).val()));
            });
            this.settingsCoordinator.updateSetting('movingAverages', 'standardMAs', selectedMAs);
        });

        // Custom MA management - integrate with coordinated settings
        $('#add-custom-ma').click(() => {
            const period = parseInt($('#custom-ma-input').val());
            if (this.state.addCustomMovingAverage(period)) {
                $('#custom-ma-input').val('');
                this.ui.updateCustomMADisplay(this.state.customMAs);
                // Update coordinated settings
                this.settingsCoordinator.updateSetting('movingAverages', 'customMAs', [...this.state.customMAs]);
            }
        });

        $('#custom-ma-input').keypress((e) => {
            if (e.which === 13) {
                $('#add-custom-ma').click();
            }
        });

        // Remove custom MA - integrate with coordinated settings
        $(document).on('click', '.remove-custom-ma', (e) => {
            const period = parseInt($(e.currentTarget).data('period'));
            if (this.state.removeCustomMovingAverage(period)) {
                this.ui.updateCustomMADisplay(this.state.customMAs);
                // Update coordinated settings
                this.settingsCoordinator.updateSetting('movingAverages', 'customMAs', [...this.state.customMAs]);
            }
        });

        // MA presets - use coordinated settings for atomic updates
        $('#ma-preset-none').click(() => {
            const updates = {
                'movingAverages.standardMAs': []
            };
            this.settingsCoordinator.updateMultipleSettings(updates);
            // Update DOM to reflect changes
            $('.ma-checkbox').prop('checked', false);
        });

        $('#ma-preset-basic').click(() => {
            const updates = {
                'movingAverages.standardMAs': [20, 50]
            };
            this.settingsCoordinator.updateMultipleSettings(updates);
            // Update DOM to reflect changes
            $('.ma-checkbox').prop('checked', false);
            $('#ma-20, #ma-50').prop('checked', true);
        });

        $('#ma-preset-extended').click(() => {
            const updates = {
                'movingAverages.standardMAs': [20, 50, 200]
            };
            this.settingsCoordinator.updateMultipleSettings(updates);
            // Update DOM to reflect changes
            $('.ma-checkbox').prop('checked', false);
            $('#ma-20, #ma-50, #ma-200').prop('checked', true);
        });

        $('#ma-preset-day-trading').click(() => {
            const updates = {
                'movingAverages.standardMAs': [5, 10, 20]
            };
            this.settingsCoordinator.updateMultipleSettings(updates);
            // Update DOM to reflect changes
            $('.ma-checkbox').prop('checked', false);
            $('#ma-5, #ma-10, #ma-20').prop('checked', true);
        });
    }

    setupElliottListeners() {
        // Remove Elliott point - integrate with coordinated settings
        $(document).on('click', '.remove-point', (e) => {
            const index = parseInt($(e.currentTarget).data('index'));
            this.state.elliottPoints.splice(index, 1);
            this.ui.updateElliottDisplay(this.state.elliottPoints);
            // Update coordinated settings
            this.settingsCoordinator.updateSetting('elliottWave', 'points', [...this.state.elliottPoints]);
        });

        $('#clear-elliott-points').click(() => {
            this.state.elliottPoints = [];
            this.ui.updateElliottDisplay(this.state.elliottPoints);
            // Update coordinated settings
            this.settingsCoordinator.updateSetting('elliottWave', 'points', []);
        });

        // Elliott wave enhancements - use coordinated settings
        $('#show-elliott-fib-levels').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('elliottWave', 'showFibLevels', enabled);
        });

        $('#extend-elliott-projections').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('elliottWave', 'extendProjections', enabled);
        });

        // Elliott wave auto-generation toggle - use coordinated settings
        $('#show-elliott-auto-waves').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('elliottWave', 'showAutoWaves', enabled);
        });
    }

    setupIndicatorListeners() {
        // Use coordinated settings for subplot indicators
        $('#showRSI').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('subplots', 'showRSI', enabled);
        });

        $('#showMACD').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('subplots', 'showMACD', enabled);
        });

        $('#showVolume').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('subplots', 'showVolume', enabled);
        });

        $('#showCandlestick').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('graphSettings', 'showCandlestick', enabled);
        });

        // Graph Settings listeners with coordinated settings
        $('#showGraphLines').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('graphSettings', 'showGraphLines', enabled);
            // Apply immediately for visual feedback
            this.toggleGraphLines(enabled);
        });

        $('#showTimeSelector').on('change', (e) => {
            const enabled = $(e.target).is(':checked');
            this.settingsCoordinator.updateSetting('graphSettings', 'showTimeSelector', enabled);
            // Apply immediately for visual feedback
            this.toggleTimeSelector(enabled);
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
        // Update analysis mode in coordinated settings
        this.settingsCoordinator.updateSetting('analysisMode', null, analysisMode);
        
        // Handle mode-specific logic - RSI, MACD, Volume, and Candlestick work as independent toggles
        if (analysisMode === 'rsi') {
            // Toggle RSI indicator when RSI mode is selected (don't affect others)
            const currentRSI = this.settingsCoordinator.getSetting('subplots', 'showRSI');
            this.settingsCoordinator.updateSetting('subplots', 'showRSI', !currentRSI);
        } else if (analysisMode === 'macd') {
            // Toggle MACD indicator when MACD mode is selected (don't affect others)
            const currentMACD = this.settingsCoordinator.getSetting('subplots', 'showMACD');
            this.settingsCoordinator.updateSetting('subplots', 'showMACD', !currentMACD);
        } else if (analysisMode === 'volume') {
            // Toggle Volume indicator when Volume mode is selected
            const currentVolume = this.settingsCoordinator.getSetting('subplots', 'showVolume');
            this.settingsCoordinator.updateSetting('subplots', 'showVolume', !currentVolume);
        }
        // For other modes (fib, trendlines, elliott, ma), don't change indicator settings
        // This allows all indicators to persist across all modes

        // Note: Chart refresh and visual updates are handled by the coordinated settings system
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

    toggleSettings() {
        this.ui.toggleSettings();
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

    // ========================================
    // GRAPH SETTINGS METHODS
    // ========================================

    toggleGraphLines(enabled) {
        try {
            const layout = {
                xaxis: { showgrid: enabled },
                yaxis: { showgrid: enabled }
            };
            Plotly.relayout(this.containerId, layout);
            this.saveSettingToStorage('showGraphLines', enabled);
            console.log(`Graph lines ${enabled ? 'enabled' : 'disabled'}`);
        } catch (error) {
            console.warn('Failed to update graph lines setting:', error);
            // Revert toggle state
            $('#showGraphLines').prop('checked', !enabled);
            this.ui.showError('Failed to update graph lines setting');
        }
    }

    saveSettingToStorage(key, value) {
        try {
            localStorage.setItem(`chart_${key}`, JSON.stringify(value));
        } catch (error) {
            console.warn('Failed to save setting to localStorage:', error);
        }
    }

    loadSettingFromStorage(key, defaultValue = false) {
        try {
            const stored = localStorage.getItem(`chart_${key}`);
            return stored ? JSON.parse(stored) : defaultValue;
        } catch (error) {
            console.warn('Failed to load setting from localStorage:', error);
            return defaultValue;
        }
    }

    initializeGraphSettings() {
        // Load saved settings and set toggle states (don't apply to chart yet)
        const showGraphLines = this.loadSettingFromStorage('showGraphLines', true);
        const showTimeSelector = this.loadSettingFromStorage('showTimeSelector', false);
        
        $('#showGraphLines').prop('checked', showGraphLines);
        $('#showTimeSelector').prop('checked', showTimeSelector);
        
        console.log(`Graph settings initialized - Graph Lines: ${showGraphLines}, Time Selector: ${showTimeSelector}`);
    }

    toggleTimeSelector(enabled) {
        try {
            // Get current layout to check for existing subplots
            const graphDiv = document.getElementById(this.containerId);
            if (!graphDiv || !graphDiv.layout) {
                console.warn('Chart not ready for time selector toggle');
                return;
            }

            // For now, disable time selector when subplots are present to avoid conflicts
            const hasSubplots = graphDiv.layout.yaxis2 || graphDiv.layout.yaxis3 || graphDiv.layout.yaxis4;
            
            if (enabled && hasSubplots) {
                console.warn('Time selector disabled when subplots (RSI, MACD, Volume) are present');
                $('#showTimeSelector').prop('checked', false);
                this.ui.showError('Time selector is not compatible with technical indicators. Please disable RSI, MACD, or Volume first.');
                return;
            }

            const layout = {
                xaxis: { 
                    rangeslider: { 
                        visible: enabled,
                        thickness: enabled ? 0.15 : 0
                    }
                }
            };

            Plotly.relayout(this.containerId, layout);
            this.saveSettingToStorage('showTimeSelector', enabled);
            console.log(`Time selector ${enabled ? 'enabled' : 'disabled'}`);
        } catch (error) {
            console.warn('Failed to update time selector setting:', error);
            // Revert toggle state
            $('#showTimeSelector').prop('checked', !enabled);
            this.ui.showError('Failed to update time selector setting');
        }
    }

    applyGraphSettings() {
        // Apply graph settings to the rendered chart
        const showGraphLines = $('#showGraphLines').is(':checked');
        if (showGraphLines !== undefined) {
            this.toggleGraphLines(showGraphLines);
        }

        const showTimeSelector = $('#showTimeSelector').is(':checked');
        if (showTimeSelector !== undefined) {
            this.toggleTimeSelector(showTimeSelector);
        }
    }
}

// Export for use in other modules
window.StockChart = StockChart;