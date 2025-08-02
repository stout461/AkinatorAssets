# Implementation Plan

- [x] 1. Refactor HTML structure for two-row analysis modes layout





  - Modify the analysis modes section in `src/templates/components/stock_chart.html` to implement two-row layout with 4 items in first row and 3 in second row
  - Remove candlestick mode from analysis modes section
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Add new Graph Settings section to HTML template



  - Create new Graph Settings section with same visual styling as Analysis Modes section
  - Add candlestick toggle (moved from analysis modes)
  - Add new graph lines toggle for main price graph
  - Add new subplot time selector toggle
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Update CSS styles for two-row analysis modes layout



  - Add CSS classes for `.mode-tabs-container` and `.mode-tabs-row` in `src/static/css/chart.css`
  - Implement responsive styling for first row (4 items) and second row (3 items)
  - Ensure visual consistency with existing design
  - _Requirements: 1.5, 5.1, 5.2_

- [x] 4. Add CSS styles for Graph Settings section







  - Create styles for `.graph-settings-section` with consistent visual design
  - Style the graph settings controls container
  - Ensure proper spacing and alignment for the three toggles
  - _Requirements: 2.2, 5.3, 5.4_

- [x] 5. Implement JavaScript functionality for graph lines toggle



  - Add `toggleGraphLines()` method to StockChart class in `src/static/js/chart.js`
  - Implement Plotly layout updates for showing/hiding grid lines on main price graph
  - Add event handler for graph lines toggle
  - Implement settings persistence using localStorage
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Implement JavaScript functionality for subplot time selector toggle





  - Add `toggleTimeSelector()` method to StockChart class in `src/static/js/chart.js`
  - Implement Plotly layout updates for showing/hiding rangeslider subplot
  - Add event handler for time selector toggle
  - Implement settings persistence using localStorage
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [x] 7. Update candlestick toggle integration for new location



  - Move candlestick toggle event handler to work with new Graph Settings section
  - Ensure existing candlestick functionality works seamlessly from new location
  - Test compatibility with time selector when both are enabled
  - _Requirements: 2.3, 4.4_

- [ ] 9. Implement settings state management and persistence








  - Update settings object structure to include new graph settings
  - Add localStorage keys for new settings (graph lines and time selector)
  - Implement loading of saved settings on page initialization
  - Add error handling for localStorage failures with fallback to defaults
  - _Requirements: 3.4, 4.5_

- [ ] 10. Add comprehensive testing and error handling
  - Add try-catch blocks around Plotly layout updates with user feedback
  - Test all combinations of settings (candlestick + time selector, etc.)
  - Verify settings persistence across page reloads
  - Test responsive behavior on different screen sizes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_