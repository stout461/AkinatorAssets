/**
 * Dashboard-specific JavaScript
 * Handles dashboard initialization and chart integration
 */

console.log("✅ dashboard.js loaded");

// Initialize dashboard when page loads
$(document).ready(function () {
    // Initialize the compact chart for the dashboard
    window.dashboardChart = createStockChart('graph', 'compact');

    // Override navigation methods for dashboard context
    window.dashboardChart.navigateToDetailed = function () {
        const ticker = $('#ticker').val().trim();
        const period = $('input[name="period"]:checked').val();
        if (ticker) {
            // Save current state before navigation
            const state = this.getChartState();
            localStorage.setItem('chartState', JSON.stringify(state));

            // Navigate to detailed view
            window.location.href = `/detailed-graph/${ticker}?period=${period}`;
        } else {
            alert('Please enter a ticker symbol first');
        }
    };

    // Integrate with existing loadAllData function
    const originalLoadAllData = window.loadAllData;
    window.loadAllData = function () {
        const params = window.dashboardChart.getCommonFetchParams();

        if (!params.ticker) {
            $('#error').text('Please enter a valid ticker symbol').show();
            return;
        }

        // Reset all sections
        resetMOATAnalysis();
        $('#analysis-container').hide();
        $('#error').hide();

        // Fetch all in parallel, including chart
        Promise.all([
            window.dashboardChart.loadChartData().then(response => {
                if (response && !response.error) {
                    updatePriceStats(response);
                    updateFinancialMetrics(response);
                    initUserProjections(response);
                    $('#stats-container').show();
                    $('#price-target-container').show();
                }
                return response;
            }),
            fetchAnalysis(),
            fetchMOATAnalysis()
        ]).then(() => {
            console.log('✅ All data loaded with new chart component');
        }).catch(error => {
            console.error('Error loading data:', error);
        });
    };

    console.log('✅ Dashboard chart component initialized');
});