# Requirements Document

## Introduction

This feature involves refactoring the existing graph settings UI to improve organization and usability. Currently, all settings are grouped under a single "Analysis Modes" section. The refactoring will separate analysis modes from graph display settings, reorganize the analysis modes into a more structured layout, and add new graph display features including graph lines toggle and subplot time selector toggle.

## Requirements

### Requirement 1

**User Story:** As a user, I want the analysis modes to be organized in a cleaner two-row layout, so that I can more easily navigate between different analysis tools.

#### Acceptance Criteria

1. WHEN the settings panel is opened THEN the analysis modes SHALL be displayed in two rows
2. WHEN viewing the first row THEN it SHALL contain exactly 4 analysis mode items (Fibonacci, Trendlines, Elliott, Moving Avg)
3. WHEN viewing the second row THEN it SHALL contain exactly 3 analysis mode items (RSI, MACD, Volume)
4. WHEN the analysis modes are displayed THEN the candlestick mode SHALL NOT be included in the analysis modes section
5. WHEN the layout is rendered THEN the two-row structure SHALL maintain visual consistency with the existing design

### Requirement 2

**User Story:** As a user, I want a separate "Graph Settings" section for display-related controls, so that I can distinguish between analysis tools and graph display options.

#### Acceptance Criteria

1. WHEN the settings panel is opened THEN there SHALL be a new section titled "Graph Settings"
2. WHEN viewing the Graph Settings section THEN it SHALL be formatted with the same visual style as the Analysis Modes section
3. WHEN the Graph Settings section is displayed THEN it SHALL contain the candlestick toggle (moved from analysis modes)
4. WHEN the Graph Settings section is displayed THEN it SHALL contain a new graph lines toggle for the main price graph
5. WHEN the Graph Settings section is displayed THEN it SHALL contain a new subplot time selector toggle

### Requirement 3

**User Story:** As a user, I want to toggle graph lines on the main price graph, so that I can customize the visual appearance of the price data.

#### Acceptance Criteria

1. WHEN the graph lines toggle is enabled THEN grid lines SHALL be displayed on the main price graph
2. WHEN the graph lines toggle is disabled THEN grid lines SHALL be hidden on the main price graph
3. WHEN the toggle state changes THEN the graph SHALL update immediately without requiring a full reload
4. WHEN the page is refreshed THEN the graph lines toggle state SHALL be preserved
5. WHEN the toggle is interacted with THEN it SHALL provide visual feedback consistent with other toggles

### Requirement 4

**User Story:** As a user, I want to toggle the subplot time selector, so that I can choose whether to display the time navigation control that comes with candlestick charts.

#### Acceptance Criteria

1. WHEN the subplot time selector toggle is enabled THEN the time selector subplot SHALL be displayed
2. WHEN the subplot time selector toggle is disabled THEN the time selector subplot SHALL be hidden
3. WHEN the toggle state changes THEN the chart layout SHALL adjust immediately
4. WHEN candlestick mode is active AND subplot time selector is enabled THEN both features SHALL work together seamlessly
5. WHEN the page is refreshed THEN the subplot time selector toggle state SHALL be preserved

### Requirement 5

**User Story:** As a user, I want the refactored settings to maintain the same responsive behavior, so that the interface works well on all device sizes.

#### Acceptance Criteria

1. WHEN viewing on mobile devices THEN the two-row analysis modes layout SHALL adapt appropriately
2. WHEN viewing on tablet devices THEN both Analysis Modes and Graph Settings sections SHALL remain accessible
3. WHEN the screen size changes THEN the settings layout SHALL adjust without breaking functionality
4. WHEN using touch interactions THEN all toggles and controls SHALL remain easily accessible
5. WHEN the settings panel is displayed on small screens THEN it SHALL not cause horizontal scrolling