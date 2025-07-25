# Design Document

## Overview

This design outlines a centralized subplot management system that will replace the current scattered approach to handling chart subplots. The system will provide intelligent layout calculation, conflict resolution, and a clean API for coordinating between frontend settings and backend subplot creation. The architecture will be extensible, allowing new technical indicators to be added easily while maintaining optimal chart layouts.

## Architecture

### Current Problems Analysis
1. **Scattered Logic**: Subplot creation logic is mixed throughout `create_stock_plot()` function
2. **Manual Row Management**: Each subplot manually calculates its row position and height
3. **Frontend/Backend Disconnect**: Frontend toggles don't coordinate with backend layout decisions
4. **Conflict Resolution**: No systematic approach to handling incompatible feature combinations
5. **Scalability**: Adding new indicators requires modifying multiple code locations

### New Architecture Overview
The new system will consist of three main components:
1. **Backend SubplotManager**: Centralized subplot configuration and layout calculation
2. **Frontend SettingsCoordinator**: Unified settings management and conflict detection
3. **API Layer**: Clean communication interface between frontend and backend

## Components and Interfaces

### 1. Backend SubplotManager Class

#### Core Structure
```python
class SubplotManager:
    def __init__(self):
        self.subplot_configs = {
            'volume': {
                'height_ratio': 0.2,
                'title': 'Volume',
                'show_grid': False,
                'y_axis_title': 'Volume',
                'priority': 1,
                'conflicts_with': [],
                'requires': []
            },
            'rsi': {
                'height_ratio': 0.2,
                'title': 'RSI',
                'show_grid': False,
                'y_axis_title': 'RSI (0-100)',
                'priority': 2,
                'conflicts_with': [],
                'requires': []
            },
            'macd': {
                'height_ratio': 0.25,
                'title': 'MACD',
                'show_grid': False,
                'y_axis_title': 'MACD',
                'priority': 3,
                'conflicts_with': [],
                'requires': []
            },
            'time_selector': {
                'height_ratio': 0.15,
                'title': '',
                'show_grid': False,
                'y_axis_title': '',
                'priority': 4,
                'conflicts_with': ['rsi', 'macd', 'volume'],
                'requires': []
            }
        }
        self.max_subplots = 3  # Reasonable limit for readability
        self.min_price_height = 0.4  # Minimum height for price chart
```

#### Key Methods
```python
def calculate_layout(self, requested_subplots):
    """
    Calculate optimal subplot layout based on requested indicators.
    
    Args:
        requested_subplots: List of subplot names to include
        
    Returns:
        dict: Layout configuration with rows, heights, and metadata
    """
    
def validate_subplot_combination(self, requested_subplots):
    """
    Validate that requested subplot combination is feasible.
    
    Returns:
        dict: Validation result with conflicts and suggestions
    """
    
def create_subplot_figure(self, requested_subplots, **kwargs):
    """
    Create Plotly figure with calculated subplot layout.
    
    Returns:
        plotly.graph_objects.Figure: Configured subplot figure
    """
    
def add_subplot_data(self, fig, subplot_name, data, row):
    """
    Add data traces to specific subplot.
    
    Args:
        fig: Plotly figure object
        subplot_name: Name of subplot to add data to
        data: Data to plot
        row: Row number for the subplot
    """
```

### 2. Frontend SettingsCoordinator Class

#### Core Structure
```javascript
class SettingsCoordinator {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.currentSettings = {
            subplots: [],
            graphSettings: {
                showCandlestick: false,
                showGraphLines: true,
                showTimeSelector: false
            }
        };
        this.conflictRules = {
            time_selector: ['rsi', 'macd', 'volume']
        };
    }
    
    validateSettings(newSettings) {
        // Check for conflicts and return validation result
    }
    
    applySettings(settings) {
        // Apply validated settings to chart
    }
    
    getOptimalConfiguration(requestedFeatures) {
        // Suggest optimal configuration for requested features
    }
}
```

### 3. Enhanced API Interface

#### Request Format
```python
# New unified subplot request format
subplot_request = {
    'subplots': ['volume', 'rsi'],  # List of requested subplots
    'graph_settings': {
        'show_candlestick': True,
        'show_graph_lines': True,
        'show_time_selector': False
    },
    'layout_preferences': {
        'max_subplots': 3,
        'min_price_height': 0.4
    }
}
```

#### Response Format
```python
# Enhanced response with layout metadata
response = {
    'figure': plotly_figure_json,
    'layout_info': {
        'subplot_rows': {
            'price': 1,
            'volume': 2,
            'rsi': 3
        },
        'height_ratios': [0.6, 0.2, 0.2],
        'conflicts_resolved': [],
        'suggestions': []
    },
    'validation_result': {
        'valid': True,
        'conflicts': [],
        'warnings': []
    }
}
```

## Data Models

### SubplotConfiguration
```python
@dataclass
class SubplotConfiguration:
    name: str
    height_ratio: float
    title: str
    show_grid: bool
    y_axis_title: str
    priority: int
    conflicts_with: List[str]
    requires: List[str]
    renderer_function: callable
```

### LayoutResult
```python
@dataclass
class LayoutResult:
    subplot_rows: Dict[str, int]
    height_ratios: List[float]
    total_rows: int
    price_chart_domain: Tuple[float, float]
    conflicts_resolved: List[str]
    warnings: List[str]
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    valid: bool
    conflicts: List[Dict[str, Any]]
    suggestions: List[str]
    max_subplots_exceeded: bool
    alternative_configs: List[Dict[str, Any]]
```

## Error Handling

### Conflict Resolution Strategies
1. **Priority-Based Resolution**: Higher priority indicators take precedence
2. **User Choice**: Present conflict options to user for manual resolution
3. **Automatic Fallback**: Disable conflicting features with user notification
4. **Alternative Suggestions**: Suggest compatible feature combinations

### Error Recovery
```python
class SubplotError(Exception):
    def __init__(self, message, conflicts=None, suggestions=None):
        super().__init__(message)
        self.conflicts = conflicts or []
        self.suggestions = suggestions or []

def handle_subplot_error(error):
    """
    Graceful error handling with user feedback and fallback options.
    """
    return {
        'error': str(error),
        'conflicts': error.conflicts,
        'suggestions': error.suggestions,
        'fallback_config': get_safe_fallback_config()
    }
```

## Testing Strategy

### Unit Tests
1. **SubplotManager Tests**: Layout calculation, conflict detection, validation
2. **Configuration Tests**: Subplot config validation and parsing
3. **Layout Algorithm Tests**: Height calculation and row assignment
4. **Conflict Resolution Tests**: All conflict scenarios and resolutions

### Integration Tests
1. **Frontend/Backend Coordination**: Settings synchronization
2. **Chart Rendering**: Subplot figure creation and data addition
3. **Dynamic Updates**: Adding/removing subplots without full reload
4. **Error Handling**: Graceful degradation and user feedback

### Performance Tests
1. **Layout Calculation Speed**: Ensure fast response for complex configurations
2. **Memory Usage**: Monitor memory consumption with multiple subplots
3. **Rendering Performance**: Chart update speed with dynamic subplot changes

## Implementation Phases

### Phase 1: Backend SubplotManager Foundation
- Create `SubplotManager` class with basic configuration system
- Implement layout calculation algorithms
- Add conflict detection and validation logic
- Create unit tests for core functionality

### Phase 2: API Integration
- Modify `create_stock_plot()` to use `SubplotManager`
- Update Flask endpoints to handle new request format
- Implement enhanced response format with layout metadata
- Add error handling and validation

### Phase 3: Frontend SettingsCoordinator
- Create `SettingsCoordinator` class for unified settings management
- Update chart.js to use coordinated settings approach
- Implement conflict detection and user feedback in frontend
- Add settings persistence and restoration

### Phase 4: Advanced Features
- Implement intelligent conflict resolution strategies
- Add support for custom subplot configurations
- Create extensible plugin system for new indicators
- Add advanced layout optimization algorithms

### Phase 5: Testing and Optimization
- Comprehensive testing of all subplot combinations
- Performance optimization for complex layouts
- User experience testing and refinement
- Documentation and developer guides

## Migration Strategy

### Backward Compatibility
- Maintain existing API endpoints during transition
- Provide adapter layer for current frontend code
- Gradual migration of individual subplot types
- Feature flags for enabling new system components

### Data Migration
- Convert existing subplot configurations to new format
- Migrate user preferences and saved settings
- Update any stored chart configurations
- Provide fallback for unsupported legacy configurations

## Benefits of New Architecture

### For Developers
1. **Single Source of Truth**: All subplot logic centralized
2. **Easy Extension**: New indicators require minimal code changes
3. **Better Testing**: Isolated components are easier to test
4. **Cleaner Code**: Separation of concerns and reduced complexity

### For Users
1. **Better Performance**: Optimized layout calculations
2. **Consistent Behavior**: Predictable subplot behavior
3. **Intelligent Conflicts**: Automatic resolution of incompatible features
4. **Enhanced UX**: Clear feedback and suggestions for optimal configurations

### For System
1. **Scalability**: Easy to add new subplot types
2. **Maintainability**: Centralized logic is easier to maintain
3. **Reliability**: Better error handling and validation
4. **Flexibility**: Configurable layout preferences and constraints