# Implementation Plan

- [x] 1. Create reusable chart component template



  - Create `src/templates/components/stock_chart.html` with parameterized chart HTML
  - Extract all chart-related HTML from `index.html` into the component
  - Add parameters for chart mode (compact/detailed), container ID, and control visibility
  - _Requirements: 2.1, 2.2_




- [x] 2. Extract chart JavaScript into separate module





  - Create `src/static/js/chart.js` with StockChart class
  - Move all chart-related JavaScript functions from existing script files

  - Implement chart initialization, data loading, and settings management
  - Add support for different chart modes and sizing
  - _Requirements: 2.2, 2.3_

- [x] 3. Create chart-specific CSS styles


  - Create `src/static/css/chart.css` for chart styling
  - Add responsive styles for both compact and detailed modes
  - Implement full-screen chart layout styles
  - Add styles for chart controls and settings panels
  - _Requirements: 4.1, 4.2_

- [x] 4. Modify main dashboard template



  - Update `src/templates/index.html` to use the chart component
  - Add "Detailed Graph" button near the existing chart



  - Ensure compact chart maintains current sizing and functionality
  - Include new chart CSS and JS files
  - _Requirements: 1.1, 3.1, 3.2_

- [x] 5. Create detailed graph page template

  - Create `src/templates/detailed_graph.html` for full-screen chart view
  - Use the same chart component with detailed mode parameters
  - Add navigation controls to return to main dashboard
  - Include ticker input and period selection controls
  - Implement full-screen layout (80%+ viewport coverage)
  - _Requirements: 1.2, 1.3, 4.1, 4.2_

- [x] 6. Add Flask route for detailed graph page



  - Add `/detailed-graph/<ticker>` route to `src/akinator_assets.py`
  - Accept optional query parameters for period and chart settings
  - Render detailed graph template with ticker context
  - Handle invalid ticker parameters gracefully
  - _Requirements: 1.1, 3.3_

- [x] 7. Implement state preservation between pages



  - Add JavaScript functions to preserve chart settings in localStorage
  - Implement ticker and period state management
  - Ensure settings persist when navigating between pages
  - Add URL parameter handling for direct links to detailed view
  - _Requirements: 3.3, 3.4_

- [x] 8. Add keyboard shortcuts for detailed graph page





  - Implement keyboard shortcuts for common chart actions
  - Add shortcuts for changing chart modes (F, T, E for Fibonacci, Trendlines, Elliott)
  - Add shortcuts for toggling settings panel (S key)
  - Add escape key to return to main dashboard
  - _Requirements: 4.4_

- [ ] 9. Test chart component integration
  - Verify chart component renders correctly in both compact and detailed modes
  - Test all existing chart functionality (Fibonacci, trendlines, Elliott waves, moving averages)
  - Ensure no regression in main dashboard functionality
  - Test navigation between pages maintains chart state
  - _Requirements: 2.4, 3.4_

- [ ] 10. Implement responsive design for detailed graph
  - Test detailed graph page on different screen sizes
  - Ensure chart controls remain accessible on mobile devices
  - Implement touch-friendly interactions for mobile users
  - Add responsive breakpoints for optimal viewing
  - _Requirements: 4.1, 4.2_