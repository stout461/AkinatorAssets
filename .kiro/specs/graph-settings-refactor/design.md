# Design Document

## Overview

This design outlines the refactoring of the graph settings UI to separate analysis modes from graph display settings, reorganize the analysis modes into a two-row layout, and introduce new graph display features. The refactoring will improve user experience by creating logical groupings of related functionality while maintaining the existing visual design language.

## Architecture

### Current Structure Analysis
The existing settings are contained within a single `.settings-single-row` container with:
- One `.settings-section.modes-section` containing all analysis modes including candlestick
- One `.settings-section.mode-specific` for mode-specific settings

### New Structure Design
The refactored structure will have:
- **Analysis Modes Section**: Two-row layout with 7 modes (4 in first row, 3 in second row)
- **Graph Settings Section**: New section for display-related controls
- **Mode-Specific Settings**: Remains unchanged for backward compatibility

## Components and Interfaces

### 1. Analysis Modes Section Restructure

#### HTML Structure Changes
```html
<div class="settings-section modes-section">
    <div class="section-header">
        <i class="fas fa-sliders-h"></i>
        <span>Analysis Modes</span>
    </div>
    <div class="section-content">
        <div class="mode-tabs-container">
            <!-- First Row: 4 items -->
            <div class="mode-tabs-row">
                <input type="radio" name="analysisMode" id="fibMode" value="fib" checked>
                <label for="fibMode" class="mode-tab">...</label>
                
                <input type="radio" name="analysisMode" id="trendlinesMode" value="trendlines">
                <label for="trendlinesMode" class="mode-tab">...</label>
                
                <input type="radio" name="analysisMode" id="elliottMode" value="elliott">
                <label for="elliottMode" class="mode-tab">...</label>
                
                <input type="radio" name="analysisMode" id="rsiMode" value="rsi">
                <label for="rsiMode" class="mode-tab mode-indicator">...</label>
            </div>
            
            <!-- Second Row: 3 items -->
            <div class="mode-tabs-row">
                <input type="radio" name="analysisMode" id="macdMode" value="macd">
                <label for="macdMode" class="mode-tab mode-indicator">...</label>
                
                <input type="radio" name="analysisMode" id="volumeMode" value="volume">
                <label for="volumeMode" class="mode-tab mode-indicator">...</label>
                
                <input type="radio" name="analysisMode" id="maMode" value="ma">
                <label for="maMode" class="mode-tab">...</label>
            </div>
        </div>
    </div>
</div>
```

#### CSS Design for Two-Row Layout
```css
.mode-tabs-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mode-tabs-row {
    display: flex;
    gap: 6px;
    justify-content: flex-start;
    flex-wrap: wrap;
}

.mode-tabs-row:first-child .mode-tab {
    /* First row: 4 items with equal spacing */
    flex: 1;
    min-width: 65px;
    max-width: 75px;
}

.mode-tabs-row:last-child .mode-tab {
    /* Second row: 3 items with equal spacing */
    flex: 1;
    min-width: 85px;
    max-width: 95px;
}
```

### 2. Graph Settings Section

#### HTML Structure
```html
<div class="settings-section graph-settings-section">
    <div class="section-header">
        <i class="fas fa-chart-line"></i>
        <span>Graph Settings</span>
    </div>
    <div class="section-content">
        <div class="graph-settings-controls">
            <!-- Candlestick Toggle (moved from analysis modes) -->
            <label class="compact-toggle">
                <input type="checkbox" id="showCandlestick">
                <span class="toggle-slider-mini"></span>
                <span class="toggle-text">Candlesticks</span>
            </label>
            
            <!-- New Graph Lines Toggle -->
            <label class="compact-toggle">
                <input type="checkbox" id="showGraphLines">
                <span class="toggle-slider-mini"></span>
                <span class="toggle-text">Graph Lines</span>
            </label>
            
            <!-- New Subplot Time Selector Toggle -->
            <label class="compact-toggle">
                <input type="checkbox" id="showTimeSelector">
                <span class="toggle-slider-mini"></span>
                <span class="toggle-text">Time Selector</span>
            </label>
        </div>
    </div>
</div>
```

#### CSS Design for Graph Settings
```css
.settings-section.graph-settings-section {
    min-width: 180px;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border: 2px solid #17a2b8; /* Info blue color for graph settings */
}

.graph-settings-controls {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-settings-controls .compact-toggle {
    padding: 2px 0;
}
```

### 3. JavaScript Integration Points

#### Chart.js Integration
```javascript
// New methods to be added to StockChart class
class StockChart {
    // Existing methods...
    
    toggleGraphLines(enabled) {
        const layout = {
            xaxis: { showgrid: enabled },
            yaxis: { showgrid: enabled }
        };
        Plotly.relayout(this.chartId, layout);
        this.saveSettingToStorage('showGraphLines', enabled);
    }
    
    toggleTimeSelector(enabled) {
        const layout = {
            xaxis: { 
                rangeslider: { visible: enabled }
            }
        };
        Plotly.relayout(this.chartId, layout);
        this.saveSettingToStorage('showTimeSelector', enabled);
    }
    
    // Updated candlestick method to work with new location
    toggleCandlestick(enabled) {
        // Existing candlestick logic remains the same
        // Just needs to be triggered from new location
    }
}
```

#### Event Handlers
```javascript
// New event handlers for graph settings
$('#showGraphLines').change(function() {
    const enabled = $(this).is(':checked');
    window.chartInstance.toggleGraphLines(enabled);
});

$('#showTimeSelector').change(function() {
    const enabled = $(this).is(':checked');
    window.chartInstance.toggleTimeSelector(enabled);
});

// Updated candlestick handler for new location
$('#showCandlestick').change(function() {
    const enabled = $(this).is(':checked');
    window.chartInstance.toggleCandlestick(enabled);
});
```

## Data Models

### Settings State Management
```javascript
// Extended settings object structure
const chartSettings = {
    analysisMode: 'fib', // Current analysis mode
    graphSettings: {
        showCandlestick: false,
        showGraphLines: true,
        showTimeSelector: false
    },
    // Existing mode-specific settings remain unchanged
    fibSettings: { ... },
    trendlineSettings: { ... },
    // etc.
};
```

### Local Storage Schema
```javascript
// Storage keys for new settings
const STORAGE_KEYS = {
    SHOW_GRAPH_LINES: 'chart_show_graph_lines',
    SHOW_TIME_SELECTOR: 'chart_show_time_selector',
    SHOW_CANDLESTICK: 'chart_show_candlestick' // Existing key, no change needed
};
```

## Error Handling

### Graceful Degradation
1. **Missing Plotly Features**: If rangeslider or grid options are not available, disable the respective toggles with user notification
2. **Storage Failures**: Fall back to default settings if localStorage is unavailable
3. **Layout Conflicts**: Ensure time selector and other subplot features don't conflict

### Error Recovery
```javascript
try {
    Plotly.relayout(this.chartId, layout);
} catch (error) {
    console.warn('Failed to update chart layout:', error);
    // Revert toggle state
    $('#showGraphLines').prop('checked', !enabled);
    this.showError('Failed to update graph lines setting');
}
```

## Testing Strategy

### Unit Tests
1. **Settings State Management**: Test saving/loading of new settings
2. **Toggle Functionality**: Test each new toggle independently
3. **Layout Updates**: Test Plotly layout changes for each setting

### Integration Tests
1. **Cross-Feature Compatibility**: Test candlestick + time selector combinations
2. **Responsive Behavior**: Test layout on different screen sizes
3. **State Persistence**: Test settings persistence across page reloads

### User Acceptance Tests
1. **Visual Layout**: Verify two-row analysis modes layout
2. **Graph Settings Section**: Verify new section appears and functions correctly
3. **Feature Functionality**: Test each new toggle produces expected visual changes
4. **Mobile Responsiveness**: Test on mobile devices for usability

## Implementation Phases

### Phase 1: HTML Structure Refactoring
- Modify `stock_chart.html` to implement two-row analysis modes layout
- Add new Graph Settings section with three toggles
- Remove candlestick from analysis modes

### Phase 2: CSS Updates
- Add styles for `.mode-tabs-container` and `.mode-tabs-row`
- Add styles for `.graph-settings-section`
- Update responsive breakpoints for new layout

### Phase 3: JavaScript Integration
- Add new toggle event handlers
- Implement `toggleGraphLines()` and `toggleTimeSelector()` methods
- Update settings persistence logic
- Move candlestick toggle logic to new location

### Phase 4: Testing and Refinement
- Test all combinations of settings
- Verify responsive behavior
- Ensure backward compatibility with existing functionality