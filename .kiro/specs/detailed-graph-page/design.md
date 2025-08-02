# Design Document

## Overview

This design implements a modular charting system that separates chart functionality into reusable components while providing both compact and detailed viewing experiences. The solution uses Flask template inheritance and JavaScript modules to achieve clean code organization.

## Architecture

### Component Structure
```
src/
├── templates/
│   ├── index.html (modified)
│   ├── login.html (existing)
│   ├── detailed_graph.html (new)
│   └── components/
│       └── stock_chart.html (new)
├── static/
│   ├── js/
│   │   ├── chart.js (new - extracted chart logic)
│   │   └── script.js (existing - main app logic)
│   └── css/
│       └── chart.css (new - chart-specific styles)
└── akinator_assets.py (modified - new route)
```

### Template Hierarchy
- `index.html` - Main dashboard (includes chart component)
- `detailed_graph.html` - Full-screen chart page (includes chart component)
- `components/stock_chart.html` - Reusable chart component

## Components and Interfaces

### 1. Chart Component (`components/stock_chart.html`)
**Purpose:** Reusable chart template with configurable sizing
**Parameters:**
- `chart_mode`: 'compact' | 'detailed'
- `chart_id`: Unique identifier for the chart container
- `show_controls`: Boolean for displaying chart controls

**Interface:**
```html
{% macro render_chart(chart_mode='compact', chart_id='graph', show_controls=true) %}
<!-- Chart HTML structure -->
{% endmacro %}
```

### 2. Chart JavaScript Module (`static/js/chart.js`)
**Purpose:** Encapsulated chart functionality
**Exports:**
- `initializeChart(containerId, mode)`
- `updateChart(ticker, period)`
- `toggleSettings()`
- `addMovingAverage(period)`
- `setChartMode(mode)` - 'fibonacci' | 'trendlines' | 'elliott'

**Interface:**
```javascript
class StockChart {
    constructor(containerId, mode = 'compact') {}
    async loadData(ticker, period) {}
    renderChart(data) {}
    toggleSettings() {}
    // ... other methods
}
```

### 3. Flask Routes
**New Route:** `/detailed-graph/<ticker>`
- Renders detailed graph page with pre-loaded ticker
- Accepts query parameters for period and settings

**Modified Route:** `/` (main dashboard)
- Includes chart component in compact mode

## Data Models

### Chart Configuration
```javascript
{
    ticker: string,
    period: '1M' | '3M' | '6M' | '1Y' | '5Y',
    mode: 'compact' | 'detailed',
    settings: {
        chartClickMode: 'fib' | 'trendlines' | 'elliott',
        movingAverages: number[],
        showFibonacci: boolean,
        showExtensions: boolean
    }
}
```

### Chart Data Structure
```javascript
{
    dates: string[],
    prices: number[],
    volumes: number[],
    highs: number[],
    lows: number[],
    opens: number[]
}
```

## Error Handling

### Client-Side Error Handling
- Chart loading failures with retry mechanism
- Invalid ticker validation
- Network connectivity issues
- Graceful degradation for missing data

### Server-Side Error Handling
- Invalid ticker parameter validation
- API rate limiting handling
- Database connection failures
- Template rendering errors

## Testing Strategy

### Unit Tests
- Chart component rendering with different parameters
- JavaScript chart functions (data processing, calculations)
- Flask route parameter validation
- Template macro functionality

### Integration Tests
- End-to-end chart loading workflow
- Navigation between compact and detailed views
- Chart settings persistence across page transitions
- Cross-browser compatibility testing

### Manual Testing Scenarios
1. Load main dashboard → verify compact chart displays
2. Click "Detailed Graph" → verify navigation and full-screen chart
3. Change ticker on detailed page → verify chart updates
4. Return to dashboard → verify state preservation
5. Test all chart modes (Fibonacci, trendlines, Elliott waves)
6. Test moving average functionality
7. Test responsive behavior on different screen sizes