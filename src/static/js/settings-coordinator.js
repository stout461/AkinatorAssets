/**
 * SettingsCoordinator - Unified settings management for stock charts
 * 
 * This class manages all chart settings including:
 * - Analysis modes (fib, trendlines, elliott, etc.)
 * - Graph settings (candlestick, graph lines, time selector)
 * - Subplot configurations (RSI, MACD, Volume)
 * - Moving averages and custom indicators
 * 
 * Features:
 * - Settings validation and conflict detection
 * - Intelligent conflict resolution
 * - Settings persistence and restoration
 * - Coordinated updates across all settings
 */
class SettingsCoordinator {
    constructor(chart) {
        this.chart = chart;
        this.settings = this.getDefaultSettings();
        this.conflictRules = this.initializeConflictRules();
        this.validationRules = this.initializeValidationRules();
        this.listeners = new Map(); // Event listeners for settings changes
        this.init();
    }

    init() {
        this.loadPersistedSettings();
        this.setupSettingsValidation();
        console.log('✅ SettingsCoordinator initialized');
    }

    // ========================================
    // DEFAULT SETTINGS AND CONFIGURATION
    // ========================================

    getDefaultSettings() {
        return {
            // Analysis mode settings
            analysisMode: 'fib',
            
            // Graph settings
            graphSettings: {
                showCandlestick: false,
                showGraphLines: true,
                showTimeSelector: false
            },
            
            // Subplot configuration (unified format)
            subplotConfig: {
                subplots: [],
                graph_settings: {
                    show_candlestick: false,
                    show_graph_lines: true,
                    show_time_selector: false
                },
                layout_preferences: {
                    max_subplots: 3,
                    min_price_height: 0.4
                }
            },
            
            // Individual subplot toggles (for backward compatibility)
            subplots: {
                showRSI: false,
                showMACD: false,
                showVolume: false
            },
            
            // Fibonacci settings
            fibonacciSettings: {
                manualMode: false,
                fibHigh: '',
                showExtensions: false,
                showFib: false
            },
            
            // Moving averages
            movingAverages: {
                standardMAs: [], // [20, 50, 200]
                customMAs: []
            },
            
            // Elliott wave settings
            elliottWave: {
                points: [],
                showAutoWaves: false,
                showFibLevels: false,
                extendProjections: true
            },
            
            // Trendline settings
            trendlines: {
                mode: 'off', // 'off', 'horizontal', 'point'
                persistentLines: []
            }
        };
    }

    initializeConflictRules() {
        return {
            // Time selector conflicts with subplots
            timeSelector: {
                conflictsWith: ['showRSI', 'showMACD', 'showVolume'],
                message: 'Time selector is not compatible with technical indicators',
                resolution: 'disable_time_selector'
            },
            
            // Maximum subplot limit
            maxSubplots: {
                limit: 3,
                message: 'Maximum 3 subplots allowed for optimal readability',
                resolution: 'prioritize_by_order'
            },
            
            // Analysis mode conflicts
            analysisMode: {
                // Some analysis modes may have specific requirements
                elliott: {
                    requires: [],
                    conflicts: []
                }
            }
        };
    }

    initializeValidationRules() {
        return {
            // Subplot validation
            subplots: {
                maxCount: 3,
                validTypes: ['volume', 'rsi', 'macd', 'time_selector'],
                minPriceHeight: 0.4
            },
            
            // Moving average validation
            movingAverages: {
                minPeriod: 1,
                maxPeriod: 500,
                maxCount: 10
            },
            
            // Fibonacci validation
            fibonacci: {
                fibHighRange: { min: 0, max: 10000 }
            }
        };
    }

    // ========================================
    // SETTINGS MANAGEMENT
    // ========================================

    /**
     * Update a setting with validation and conflict resolution
     * @param {string} category - Setting category (e.g., 'subplots', 'graphSettings')
     * @param {string} key - Setting key
     * @param {*} value - New value
     * @param {Object} options - Update options
     */
    updateSetting(category, key, value, options = {}) {
        const oldValue = this.getSetting(category, key);
        
        // Validate the new value
        const validation = this.validateSetting(category, key, value);
        if (!validation.valid) {
            this.handleValidationError(validation, category, key, value);
            return false;
        }

        // Check for conflicts
        const conflicts = this.detectConflicts(category, key, value);
        if (conflicts.length > 0 && !options.skipConflictResolution) {
            const resolution = this.resolveConflicts(conflicts, category, key, value);
            if (!resolution.success) {
                this.handleConflictError(resolution, conflicts);
                return false;
            }
        }

        // Apply the setting
        this.setSetting(category, key, value);
        
        // Notify listeners
        this.notifySettingChange(category, key, value, oldValue);
        
        // Persist settings
        this.persistSettings();
        
        console.log(`📊 Setting updated: ${category}.${key} = ${value}`);
        return true;
    }

    /**
     * Update multiple settings atomically
     * @param {Object} updates - Object with category.key: value pairs
     */
    updateMultipleSettings(updates) {
        const oldSettings = JSON.parse(JSON.stringify(this.settings));
        const conflicts = [];
        
        // Collect all conflicts first
        for (const [path, value] of Object.entries(updates)) {
            const [category, key] = path.split('.');
            const settingConflicts = this.detectConflicts(category, key, value);
            conflicts.push(...settingConflicts);
        }
        
        // Resolve conflicts globally
        if (conflicts.length > 0) {
            const resolution = this.resolveConflicts(conflicts);
            if (!resolution.success) {
                this.handleConflictError(resolution, conflicts);
                return false;
            }
            
            // Apply conflict resolutions
            for (const change of resolution.changes) {
                this.setSetting(change.category, change.key, change.value);
            }
        }
        
        // Apply all updates
        for (const [path, value] of Object.entries(updates)) {
            const [category, key] = path.split('.');
            this.setSetting(category, key, value);
        }
        
        // Notify all changes
        this.notifyMultipleChanges(updates, oldSettings);
        
        // Persist settings
        this.persistSettings();
        
        return true;
    }

    getSetting(category, key) {
        if (!this.settings[category]) {
            return undefined;
        }
        return key ? this.settings[category][key] : this.settings[category];
    }

    setSetting(category, key, value) {
        if (!this.settings[category]) {
            this.settings[category] = {};
        }
        if (key) {
            this.settings[category][key] = value;
        } else {
            this.settings[category] = value;
        }
    }

    getAllSettings() {
        return JSON.parse(JSON.stringify(this.settings));
    }

    resetToDefaults() {
        this.settings = this.getDefaultSettings();
        this.persistSettings();
        this.notifySettingsReset();
        console.log('📊 Settings reset to defaults');
    }

    // ========================================
    // VALIDATION SYSTEM
    // ========================================

    validateSetting(category, key, value) {
        const rules = this.validationRules[category];
        if (!rules) {
            return { valid: true };
        }

        // Subplot validation
        if (category === 'subplots') {
            return this.validateSubplotSetting(key, value, rules);
        }
        
        // Moving average validation
        if (category === 'movingAverages') {
            return this.validateMovingAverageSetting(key, value, rules);
        }
        
        // Fibonacci validation
        if (category === 'fibonacciSettings') {
            return this.validateFibonacciSetting(key, value, rules);
        }

        return { valid: true };
    }

    validateSubplotSetting(key, value, rules) {
        if (key === 'showRSI' || key === 'showMACD' || key === 'showVolume') {
            // Check maximum subplot count
            const currentSubplots = this.getActiveSubplots();
            if (value && currentSubplots.length >= rules.maxCount) {
                return {
                    valid: false,
                    error: `Maximum ${rules.maxCount} subplots allowed`,
                    suggestion: 'Disable another subplot first'
                };
            }
        }
        return { valid: true };
    }

    validateMovingAverageSetting(key, value, rules) {
        if (key === 'customMAs' && Array.isArray(value)) {
            // Validate each custom MA period
            for (const period of value) {
                if (period < rules.minPeriod || period > rules.maxPeriod) {
                    return {
                        valid: false,
                        error: `Moving average period must be between ${rules.minPeriod} and ${rules.maxPeriod}`,
                        suggestion: `Use a period between ${rules.minPeriod} and ${rules.maxPeriod}`
                    };
                }
            }
            
            // Check maximum count
            const totalMAs = this.getSetting('movingAverages', 'standardMAs').length + value.length;
            if (totalMAs > rules.maxCount) {
                return {
                    valid: false,
                    error: `Maximum ${rules.maxCount} moving averages allowed`,
                    suggestion: 'Remove some moving averages first'
                };
            }
        }
        return { valid: true };
    }

    validateFibonacciSetting(key, value, rules) {
        if (key === 'fibHigh' && value !== '') {
            const numValue = parseFloat(value);
            if (isNaN(numValue) || numValue < rules.fibHighRange.min || numValue > rules.fibHighRange.max) {
                return {
                    valid: false,
                    error: `Fibonacci high must be between ${rules.fibHighRange.min} and ${rules.fibHighRange.max}`,
                    suggestion: 'Enter a valid price level'
                };
            }
        }
        return { valid: true };
    }

    // ========================================
    // CONFLICT DETECTION AND RESOLUTION
    // ========================================

    detectConflicts(category, key, value) {
        const conflicts = [];
        
        // Time selector vs subplots conflict
        if (category === 'graphSettings' && key === 'showTimeSelector' && value) {
            const activeSubplots = this.getActiveSubplots();
            if (activeSubplots.length > 0) {
                conflicts.push({
                    type: 'time_selector_subplot_conflict',
                    conflictingSettings: ['graphSettings.showTimeSelector', ...activeSubplots.map(s => `subplots.${s}`)],
                    message: this.conflictRules.timeSelector.message,
                    resolution: this.conflictRules.timeSelector.resolution
                });
            }
        }
        
        // Subplot vs time selector conflict
        if (category === 'subplots' && value && this.getSetting('graphSettings', 'showTimeSelector')) {
            conflicts.push({
                type: 'subplot_time_selector_conflict',
                conflictingSettings: [`subplots.${key}`, 'graphSettings.showTimeSelector'],
                message: this.conflictRules.timeSelector.message,
                resolution: 'disable_time_selector'
            });
        }
        
        // Maximum subplots conflict
        if (category === 'subplots' && value) {
            const activeSubplots = this.getActiveSubplots();
            if (activeSubplots.length >= this.conflictRules.maxSubplots.limit) {
                conflicts.push({
                    type: 'max_subplots_exceeded',
                    conflictingSettings: activeSubplots.map(s => `subplots.${s}`),
                    message: this.conflictRules.maxSubplots.message,
                    resolution: this.conflictRules.maxSubplots.resolution
                });
            }
        }
        
        return conflicts;
    }

    resolveConflicts(conflicts, category = null, key = null, value = null) {
        const changes = [];
        const warnings = [];
        
        for (const conflict of conflicts) {
            switch (conflict.resolution) {
                case 'disable_time_selector':
                    changes.push({
                        category: 'graphSettings',
                        key: 'showTimeSelector',
                        value: false
                    });
                    warnings.push('Time selector disabled due to subplot conflict');
                    break;
                    
                case 'prioritize_by_order':
                    // Disable the oldest subplot to make room for new one
                    const activeSubplots = this.getActiveSubplots();
                    if (activeSubplots.length > 0) {
                        changes.push({
                            category: 'subplots',
                            key: activeSubplots[0],
                            value: false
                        });
                        warnings.push(`${activeSubplots[0]} disabled to make room for new subplot`);
                    }
                    break;
                    
                default:
                    return {
                        success: false,
                        error: `Unknown conflict resolution: ${conflict.resolution}`,
                        conflicts
                    };
            }
        }
        
        return {
            success: true,
            changes,
            warnings
        };
    }

    getActiveSubplots() {
        const subplots = this.getSetting('subplots');
        return Object.keys(subplots).filter(key => subplots[key]);
    }

    // ========================================
    // UNIFIED SUBPLOT CONFIGURATION
    // ========================================

    /**
     * Generate unified subplot configuration for API requests
     */
    generateUnifiedSubplotConfig() {
        const activeSubplots = this.getActiveSubplots();
        const subplotNames = activeSubplots.map(key => {
            // Map frontend keys to backend subplot names
            const mapping = {
                'showRSI': 'rsi',
                'showMACD': 'macd',
                'showVolume': 'volume'
            };
            return mapping[key] || key;
        });

        return {
            subplots: subplotNames,
            graph_settings: {
                show_candlestick: this.getSetting('graphSettings', 'showCandlestick'),
                show_graph_lines: this.getSetting('graphSettings', 'showGraphLines'),
                show_time_selector: this.getSetting('graphSettings', 'showTimeSelector')
            },
            layout_preferences: {
                max_subplots: this.conflictRules.maxSubplots.limit,
                min_price_height: this.validationRules.subplots.minPriceHeight
            }
        };
    }

    /**
     * Update settings from unified subplot configuration response
     */
    updateFromUnifiedConfig(config) {
        if (!config) return;

        const updates = {};
        
        // Update subplot settings
        if (config.subplots) {
            // Reset all subplots first
            updates['subplots.showRSI'] = false;
            updates['subplots.showMACD'] = false;
            updates['subplots.showVolume'] = false;
            
            // Enable active subplots
            const mapping = {
                'rsi': 'showRSI',
                'macd': 'showMACD',
                'volume': 'showVolume'
            };
            
            for (const subplot of config.subplots) {
                const frontendKey = mapping[subplot];
                if (frontendKey) {
                    updates[`subplots.${frontendKey}`] = true;
                }
            }
        }
        
        // Update graph settings
        if (config.graph_settings) {
            updates['graphSettings.showCandlestick'] = config.graph_settings.show_candlestick;
            updates['graphSettings.showGraphLines'] = config.graph_settings.show_graph_lines;
            updates['graphSettings.showTimeSelector'] = config.graph_settings.show_time_selector;
        }
        
        this.updateMultipleSettings(updates);
    }

    // ========================================
    // SETTINGS PERSISTENCE
    // ========================================

    persistSettings() {
        try {
            const settingsToSave = {
                ...this.settings,
                version: '1.0',
                timestamp: Date.now()
            };
            localStorage.setItem('stockChart_settings', JSON.stringify(settingsToSave));
            console.log('📊 Settings persisted to localStorage');
        } catch (error) {
            console.warn('Failed to persist settings:', error);
        }
    }

    loadPersistedSettings() {
        try {
            const saved = localStorage.getItem('stockChart_settings');
            if (saved) {
                const parsed = JSON.parse(saved);
                
                // Validate and migrate settings if needed
                const migrated = this.migrateSettings(parsed);
                this.settings = { ...this.getDefaultSettings(), ...migrated };
                
                console.log('📊 Settings loaded from localStorage');
                return true;
            }
        } catch (error) {
            console.warn('Failed to load persisted settings:', error);
        }
        return false;
    }

    migrateSettings(saved) {
        // Handle settings migration for different versions
        if (!saved.version) {
            // Migrate from old format
            console.log('📊 Migrating settings from old format');
            return this.migrateFromLegacyFormat(saved);
        }
        
        return saved;
    }

    migrateFromLegacyFormat(oldSettings) {
        // Convert old individual settings to new coordinated format
        const migrated = this.getDefaultSettings();
        
        // Migrate any recognizable old settings
        if (oldSettings.showRSI !== undefined) {
            migrated.subplots.showRSI = oldSettings.showRSI;
        }
        if (oldSettings.showMACD !== undefined) {
            migrated.subplots.showMACD = oldSettings.showMACD;
        }
        if (oldSettings.showVolume !== undefined) {
            migrated.subplots.showVolume = oldSettings.showVolume;
        }
        
        return migrated;
    }

    exportSettings() {
        return {
            settings: this.getAllSettings(),
            version: '1.0',
            exportDate: new Date().toISOString()
        };
    }

    importSettings(importedData) {
        try {
            if (!importedData.settings) {
                throw new Error('Invalid settings format');
            }
            
            const migrated = this.migrateSettings(importedData.settings);
            this.settings = { ...this.getDefaultSettings(), ...migrated };
            this.persistSettings();
            this.notifySettingsImported();
            
            console.log('📊 Settings imported successfully');
            return true;
        } catch (error) {
            console.error('Failed to import settings:', error);
            return false;
        }
    }

    // ========================================
    // EVENT SYSTEM
    // ========================================

    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    removeEventListener(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    notifySettingChange(category, key, newValue, oldValue) {
        this.emit('settingChanged', { category, key, newValue, oldValue });
        this.emit(`${category}.${key}Changed`, { newValue, oldValue });
    }

    notifyMultipleChanges(updates, oldSettings) {
        this.emit('multipleSettingsChanged', { updates, oldSettings });
    }

    notifySettingsReset() {
        this.emit('settingsReset', { settings: this.getAllSettings() });
    }

    notifySettingsImported() {
        this.emit('settingsImported', { settings: this.getAllSettings() });
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in settings event listener for ${event}:`, error);
                }
            });
        }
    }

    // ========================================
    // ERROR HANDLING
    // ========================================

    handleValidationError(validation, category, key, value) {
        console.warn(`Validation failed for ${category}.${key}:`, validation.error);
        
        // Show user-friendly error message with enhanced UI feedback
        if (this.chart && this.chart.ui) {
            // Try to show field-specific validation feedback first
            const fieldId = this.mapSettingToFieldId(category, key);
            if (fieldId) {
                this.chart.ui.showValidationFeedback(fieldId, validation.error, 'error');
            } else {
                // Fallback to general error message
                this.chart.ui.showError(validation.error + (validation.suggestion ? ` (${validation.suggestion})` : ''), 'warning');
            }
            
            // Show toast for immediate feedback
            this.chart.ui.showToast(`Validation Error: ${validation.error}`, 'error', 4000);
        }
        
        this.emit('validationError', { category, key, value, validation });
    }

    handleConflictError(resolution, conflicts) {
        console.warn('Conflict resolution failed:', resolution.error);
        
        // Show user-friendly error message with enhanced UI feedback
        if (this.chart && this.chart.ui) {
            // Show conflict dialog if alternatives are available
            if (conflicts.length > 0 && conflicts[0].alternatives) {
                this.chart.ui.showConflictDialog(conflicts, conflicts[0].alternatives, (selectedAlternative) => {
                    // Apply the selected alternative
                    this.updateFromUnifiedConfig({
                        subplots: selectedAlternative.subplots,
                        graph_settings: this.getSetting('graphSettings')
                    });
                    this.chart.ui.showToast(`Applied: ${selectedAlternative.description}`, 'success', 4000);
                });
            } else {
                // Fallback to error message
                this.chart.ui.showError(resolution.error, 'warning');
                this.chart.ui.showToast(`Conflict: ${resolution.error}`, 'warning', 4000);
            }
        }
        
        this.emit('conflictError', { resolution, conflicts });
    }

    /**
     * Map setting category and key to DOM field ID for validation feedback
     */
    mapSettingToFieldId(category, key) {
        const mapping = {
            'subplots': {
                'showRSI': 'showRSI',
                'showMACD': 'showMACD',
                'showVolume': 'showVolume'
            },
            'graphSettings': {
                'showCandlestick': 'showCandlestick',
                'showGraphLines': 'showGraphLines',
                'showTimeSelector': 'showTimeSelector'
            },
            'fibonacciSettings': {
                'fibHigh': 'fibHighValue',
                'manualMode': 'manualFibMode',
                'showExtensions': 'showExtensions',
                'showFib': 'showFib'
            },
            'movingAverages': {
                'customMAs': 'custom-ma-input'
            }
        };
        
        return mapping[category] && mapping[category][key] ? mapping[category][key] : null;
    }

    // ========================================
    // SETUP AND INTEGRATION
    // ========================================

    setupSettingsValidation() {
        // This method can be extended to set up additional validation
        console.log('📊 Settings validation configured');
    }

    /**
     * Sync settings with DOM elements
     */
    syncWithDOM() {
        // Sync subplot settings
        const subplots = this.getSetting('subplots');
        $('#showRSI').prop('checked', subplots.showRSI);
        $('#showMACD').prop('checked', subplots.showMACD);
        $('#showVolume').prop('checked', subplots.showVolume);
        
        // Sync graph settings
        const graphSettings = this.getSetting('graphSettings');
        $('#showCandlestick').prop('checked', graphSettings.showCandlestick);
        $('#showGraphLines').prop('checked', graphSettings.showGraphLines);
        $('#showTimeSelector').prop('checked', graphSettings.showTimeSelector);
        
        // Sync analysis mode
        const analysisMode = this.getSetting('analysisMode');
        $(`input[name="analysisMode"][value="${analysisMode}"]`).prop('checked', true);
        
        console.log('📊 Settings synced with DOM');
    }

    /**
     * Update settings from DOM elements
     */
    updateFromDOM() {
        const updates = {};
        
        // Read subplot settings from DOM
        updates['subplots.showRSI'] = $('#showRSI').is(':checked');
        updates['subplots.showMACD'] = $('#showMACD').is(':checked');
        updates['subplots.showVolume'] = $('#showVolume').is(':checked');
        
        // Read graph settings from DOM
        updates['graphSettings.showCandlestick'] = $('#showCandlestick').is(':checked');
        updates['graphSettings.showGraphLines'] = $('#showGraphLines').is(':checked');
        updates['graphSettings.showTimeSelector'] = $('#showTimeSelector').is(':checked');
        
        // Read analysis mode
        updates['analysisMode'] = $('input[name="analysisMode"]:checked').val();
        
        this.updateMultipleSettings(updates);
    }
}

// Export for use in other modules
window.SettingsCoordinator = SettingsCoordinator;

console.log("✅ settings-coordinator.js loaded");