console.log("✅ script.js loaded");
let chartDataX = [];
let pointForLine = null;
let trendLineCount = 0;

// Ticker/period listeners
$('#submit').on('click', fetchStockData);
$('#ticker').on('keypress', function(e) {
    if (e.which === 13) fetchStockData();
});
$('input[name="period"]').on('change', fetchStockData);

// Switching chart click mode toggles which settings panel is shown
$('input[name="chartClickMode"]').on('change', function() {
    const mode = getChartClickMode();
    if (mode === 'fib') {
        $('#fibSettings').show();
        $('#trendLineSettings').hide();
    } else {
        $('#fibSettings').hide();
        $('#trendLineSettings').show();
    }
});

// On page load, set up which panel is shown by default
$(document).ready(function() {
    // Existing logic for loading watchlist table

    if (cachedData && cachedCols) {
        $('#watchlist-head').empty();
        $('#watchlist-body').empty();

        cachedCols.forEach(col => {
            $('#watchlist-head').append(`<th>${col}</th>`);
        });

        cachedData.forEach(row => {
            const rowHtml = cachedCols.map(col => {
                const cellValue = row[col] !== null ? row[col] : '';

                // 🎨 Special logic for the "5Y Multibagger Rate" column
                if (col === "5Y Multibagger Rate") {
                    const rate = parseFloat(cellValue);
                    let backgroundColor = "#ffffff"; // fallback white

                    if (!isNaN(rate)) {
                        const midpoint = 1.5;
                        let intensity;

                        if (rate < midpoint) {
                            // Red gradient: closer to 0 = darker red, closer to 1.5 = lighter red
                            intensity = Math.round(255 * (rate / midpoint)); // 0 → 255
                            backgroundColor = `rgb(255, ${intensity}, ${intensity})`;
                        } else {
                            // Green gradient: closer to 1.5 = lighter green, higher = darker green
                            const greenRange = Math.min(rate - midpoint, 3.5); // cap effect above 5
                            intensity = Math.round(255 * (1 - greenRange / 2)); // closer to 1.5 = 255, higher = 0
                            backgroundColor = `rgb(${intensity}, 255, ${intensity})`;
                        }
                    }

                    return `<td class="gradient-cell" style="background-color: ${backgroundColor}">${cellValue}</td>`;
                }

                return `<td>${cellValue}</td>`;
            }).join('');

            $('#watchlist-body').append(`<tr>${rowHtml}</tr>`);
        });

        $('#watchlist-table-container').show();

        if ($.fn.DataTable.isDataTable('#watchlist-table')) {
            $('#watchlist-table').DataTable().destroy();
        }
        $('#watchlist-table').DataTable({
            pageLength: 25,  // default to 25
            lengthMenu: [10, 25, 50, 100]
        });
    }

    // ✅ Auto-trigger AAPL chart on load
    fetchStockData();
});



// Returns "fib" or "trendlines"
function getChartClickMode() {
    return $('input[name="chartClickMode"]:checked').val();
}

// Chart Click Handler
function chartClickHandler(data) {
    const clickMode = getChartClickMode();
    const clickedY = data.points[0].y;

    // If user in Fibonacci mode: set fibHighValue from click, then fetch
    if (clickMode === 'fib') {
        if ($('#manualFibMode').is(':checked')) {
            $('#fibHighValue').val(clickedY.toFixed(2));
            fetchStockData();
        }
    }
    // If user in Trendline mode: add lines
    else if (clickMode === 'trendlines') {
        const mode = $('#trendLineMode').val();
        if (mode === 'off') return;

        let clickedX = data.points[0].x;
        if (mode === 'horizontal') {
            // add horizontal line
            trendLineCount++;
            if (!chartDataX || chartDataX.length < 2) return;
            const xStart = chartDataX[0];
            const xEnd = chartDataX[chartDataX.length - 1];

            const trace = {
                x: [xStart, xEnd],
                y: [clickedY, clickedY],
                mode: 'lines',
                line: {
                    color: randomColor(),
                    width: 2,
                    dash: 'dot'
                },
                name: 'H-Line ' + trendLineCount,
                hoverinfo: 'none'
            };
            Plotly.addTraces('graph', trace);

        } else if (mode === 'point') {
            // point-to-point line
            if (!pointForLine) {
                pointForLine = {
                    x: clickedX,
                    y: clickedY
                };
            } else {
                trendLineCount++;
                const trace = {
                    x: [pointForLine.x, clickedX],
                    y: [pointForLine.y, clickedY],
                    mode: 'lines',
                    line: {
                        color: randomColor(),
                        width: 2
                    },
                    name: 'Line ' + trendLineCount,
                    hoverinfo: 'none'
                };
                Plotly.addTraces('graph', trace);
                pointForLine = null;
            }
        }
    }
}

// randomColor for drawing lines
function randomColor() {
    const colors = ['#FF5733', '#33FFCC', '#FF33A6', '#3371FF', '#FFD633', '#4CAF50'];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Fib toggles: re-fetch on changes
$('#manualFibMode').on('change', function() {
    // If unchecked, clear fibHigh
    if (!$(this).is(':checked')) {
        $('#fibHighValue').val('');
    }
    // Only fetch if we are in fib mode
    if (getChartClickMode() === 'fib') {
        fetchStockData();
    }
});
$('#showExtensions').on('change', function() {
    if (getChartClickMode() === 'fib') {
        fetchStockData();
    }
});
$('#fibHighValue').on('change', function() {
    if ($(this).val() && getChartClickMode() === 'fib') {
        fetchStockData();
    }
});

// Main fetch function
function fetchStockData() {
    var ticker = $('#ticker').val().trim();
    var period = $('input[name="period"]:checked').val();

    if (!ticker) {
        $('#error').text('Please enter a valid ticker symbol').show();
        return;
    }

    // Show loading states
    $('#loading').show();
    $('#analysis-loading').show();
    $('#error').hide();
    $('#stats-container').hide();
    $('#price-target-container').hide();
    $('#analysis-container').hide();

    const chartMode = getChartClickMode();
    const manualFib = (chartMode === 'fib') && $('#manualFibMode').is(':checked');
    const showExtensions = $('#showExtensions').is(':checked');
    const fibHigh = $('#fibHighValue').val();

    // Start both requests simultaneously
    const chartRequest = $.ajax({
        url: '/plot',
        type: 'POST',
        data: {
            ticker: ticker,
            period: period,
            chartMode: chartMode,
            manualFib: manualFib,
            showExtensions: showExtensions,
            fibHigh: fibHigh
        }
    });

    const analysisRequest = $.ajax({
        url: '/analyze_stock',
        type: 'POST',
        data: {
            ticker: ticker
        }
    });

    // Handle chart data response
    chartRequest.done(function(response) {
        $('#loading').hide();

        if (response.error) {
            $('#error').text('Chart Error: ' + response.error).show();
            return;
        }

        // Plot the chart
        const figData = JSON.parse(response.graph);
        Plotly.newPlot('graph', figData.data, figData.layout).then(function() {
            var graphDiv = document.getElementById('graph');
            graphDiv.on('plotly_click', chartClickHandler);

            if (figData.data.length > 0) {
                chartDataX = figData.data[0].x || [];
            }
        });

        // Update financial stats
        updateFinancialStats(response);
        $('#stats-container').show();
        $('#price-target-container').show();
        initUserProjections(response);
    });

    chartRequest.fail(function(error) {
        $('#loading').hide();
        $('#error').text('Chart request failed. Please try again.').show();
    });

    // Handle analysis response
    analysisRequest.done(function(response) {
        $('#analysis-loading').hide();

        if (response.success) {
            displayAnalysisResults(response);
            $('#analysis-container').show();
            console.log(`✅ Analysis completed in ${response.duration}s with ${response.search_calls} searches`);
        } else {
            displayAnalysisError(response.error);
        }
    });

    analysisRequest.fail(function(error) {
        $('#analysis-loading').hide();
        displayAnalysisError('Analysis request failed. Please check your connection and try again.');
    });
}

// New function to update financial stats
function updateFinancialStats(response) {
    $('#current-price').text(response.price.current);
    $('#period-change').text(response.price.change);
    $('#year-high').text(response.price.high);
    $('#year-low').text(response.price.low);

    $('#revenue-growth').text(response.financials.revenueGrowth);
    $('#forward-pe').text(response.financials.forwardPE);
    $('#trailing-pe').text(response.financials.trailingPE);
    $('#profit-margin').text(response.financials.profitMargin);
    $('#price-to-sales').text(response.financials.priceToSales);
    $('#total-revenue').text(response.financials.totalRevenue);
    $('#market-cap').text(response.financials.marketCap);

    $('#future-value').text(response.priceTarget.futureValue || 'N/A');
    $('#rate-increase').text(response.priceTarget.rateIncrease || 'N/A');

    if (response.priceTarget.adjustments) {
        $('#adjustment-note').text('Note: ' + response.priceTarget.adjustments).show();
    } else {
        $('#adjustment-note').hide();
    }
}

// New function to display analysis results
function displayAnalysisResults(response) {
    try {
        // Validate data structure
        if (!response || !response.success || !response.data || !response.data.sections) {
            throw new Error('Malformed API response');
        }

        const sections = response.data.sections;

        const formatAnalysisText = (text) => {
            if (!text) return '<p class="text-muted">No data available</p>';
            return text
                .replace(/## (.*?)$/gm, '<h3>$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .replace(/^/, '<p>')
                .replace(/$/, '</p>');
        };

        $('#executive-summary').html(formatAnalysisText(response.data.executive_summary));
        $('#bull-case').html(formatAnalysisText(sections.bull_case));
        $('#bear-case').html(formatAnalysisText(sections.bear_case));
        $('#analytical-reasoning').html(formatAnalysisText(sections.analytical_reasoning));

        $('#analysis-container .card-panel').addClass('analysis-success');
        console.log('✅ Analysis sections updated successfully');
    } catch (error) {
        console.error('Error formatting analysis results:', error);
        displayAnalysisError('Error formatting analysis results');
    }
}


// New function to display analysis errors
function displayAnalysisError(errorMessage) {
    const errorHtml = `
        <div class="analysis-error p-3 rounded">
            <h6>⚠️ Analysis Error</h6>
            <p>${errorMessage}</p>
            <small class="text-muted">Please try again or contact support if the issue persists.</small>
        </div>
    `;

    $('#executive-summary').html(errorHtml);
    $('#bull-case').html('<p class="text-muted">Analysis unavailable due to error above</p>');
    $('#bear-case').html('<p class="text-muted">Analysis unavailable due to error above</p>');
    $('#analytical-reasoning').html('<p class="text-muted">Analysis unavailable due to error above</p>');

    $('#analysis-container').show();
    console.error('Analysis error:', errorMessage);
}

// User projection sliders
function calculateUserProjection() {
    const userRevenueGrowth = parseFloat($('#user-revenue-growth').val()) / 100;
    const userProfitMargin = parseFloat($('#user-profit-margin').val()) / 100;
    const userPE = parseFloat($('#user-pe-ratio').val());

    $('#user-revenue-growth-value').text(Math.round(userRevenueGrowth * 100) + '%');
    $('#user-profit-margin-value').text(Math.round(userProfitMargin * 100) + '%');
    $('#user-pe-ratio-value').text(userPE.toFixed(0));

    const revenueText = $('#total-revenue').text();
    const marketCapText = $('#market-cap').text();

    if (revenueText === 'N/A' || marketCapText === 'N/A') {
        $('#user-future-value').text('N/A');
        $('#user-rate-increase').text('N/A');
        return;
    }

    let revenue = 0;
    let marketCap = 0;
    try {
        revenue = parseFloat(revenueText.replace('$', '').replace('B', '')) * 1e9;
        marketCap = parseFloat(marketCapText.replace('$', '').replace('B', '')) * 1e9;
    } catch (err) {
        console.error('Error parsing revenue/marketcap:', err);
        $('#user-future-value').text('Error');
        $('#user-rate-increase').text('Error');
        return;
    }

    const futureValue = revenue * Math.pow((1 + userRevenueGrowth), 5) * userProfitMargin * userPE;
    const futureValueBillion = (futureValue / 1e9).toFixed(2);
    const rateIncrease = (futureValue / marketCap).toFixed(2);

    $('#user-future-value').text('$' + futureValueBillion + 'B');
    $('#user-rate-increase').text(rateIncrease + 'x');
}

// Called after we fetch new data
function initUserProjections(response) {
    if (response.financials.revenueGrowth !== 'N/A') {
        const g = parseFloat(response.financials.revenueGrowth.replace('%', ''));
        if (!isNaN(g)) $('#user-revenue-growth').val(Math.max(0, Math.min(40, g)));
    }
    if (response.financials.profitMargin !== 'N/A') {
        const pm = parseFloat(response.financials.profitMargin.replace('%', ''));
        if (!isNaN(pm)) $('#user-profit-margin').val(Math.max(1, Math.min(60, pm)));
    }
    if (response.financials.trailingPE !== 'N/A') {
        const pe = parseFloat(response.financials.trailingPE);
        if (!isNaN(pe)) $('#user-pe-ratio').val(Math.max(5, Math.min(50, pe)));
    }
    calculateUserProjection();
}

// Recalculate on slider input
$('#user-revenue-growth, #user-profit-margin, #user-pe-ratio').on('input', calculateUserProjection);

// Add these functions to your script.js file

// ========================================
// MOAT ANALYSIS FUNCTIONS
// Add these to your existing script.js file
// ========================================

// MOAT Analysis Functions
function runMOATAnalysis(ticker) {
    console.log(`🏰 Starting MOAT analysis for ${ticker}`);

    // Show loading state
    showMOATLoading();

    // Make API call to backend
    fetch('/api/moat-analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: ticker })
    })
    .then(response => response.json())
    .then(data => {
        console.log('MOAT Analysis Response:', data);
        if (data.success) {
            displayMOATAnalysis(data.data);
        } else {
            showMOATError(data.error || 'MOAT analysis failed');
        }
    })
    .catch(error => {
        console.error('MOAT Analysis Error:', error);
        showMOATError('Failed to connect to MOAT analysis service');
    });
}

function showMOATLoading() {
    document.getElementById('moat-initial').style.display = 'none';
    document.getElementById('moat-content').style.display = 'none';
    document.getElementById('moat-error').style.display = 'none';
    document.getElementById('moat-loading').style.display = 'block';
}

function displayMOATAnalysis(data) {
    console.log('✅ Displaying MOAT analysis:', data);

    // Hide loading states
    document.getElementById('moat-loading').style.display = 'none';
    document.getElementById('moat-error').style.display = 'none';
    document.getElementById('moat-initial').style.display = 'none';

    // Show content
    document.getElementById('moat-content').style.display = 'block';

    // Populate sections
    populateMOATSection('moat-executive-summary', data.sections.executive_summary);
    populateMOATSection('moat-analysis-content', data.sections.moat_analysis);
    populateMOATSection('market-positioning-content', data.sections.market_positioning);
    populateMOATSection('competitive-landscape-content', data.sections.competitive_landscape);

    // Update title
    const mainTitle = document.querySelector('.col-lg-9 .card-panel h5');
    if (mainTitle && data.ticker) {
        mainTitle.innerHTML = `🏰 Competitive MOAT Analysis - ${data.ticker}`;
    }

    // Make sure first tab is active
    setTimeout(() => {
        switchMOATTab('executive');
    }, 500);
}

function populateMOATSection(elementId, content) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`❌ Element ${elementId} not found`);
        return;
    }

    if (!content || content.trim() === '') {
        element.innerHTML = '<p class="text-muted">No content available for this section.</p>';
        return;
    }

    // Format content with proper HTML
    const formattedContent = formatMOATContent(content);
    element.innerHTML = formattedContent;
}

function formatMOATContent(content) {
    let formatted = content;

    // Convert markdown-style formatting to HTML
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert bullet points
    formatted = formatted.replace(/^- (.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/^• (.*$)/gim, '<li>$1</li>');

    // Wrap consecutive list items in ul tags
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    formatted = formatted.replace(/<\/ul>\s*<ul>/g, '');

    // Convert line breaks to paragraphs
    const paragraphs = formatted.split('\n\n');
    const htmlParagraphs = paragraphs.map(p => {
        p = p.trim();
        if (p === '') return '';
        if (p.includes('<ul>') || p.includes('<li>')) return p;
        return `<p>${p}</p>`;
    }).filter(p => p !== '');

    return htmlParagraphs.join('\n');
}

function showMOATError(errorMessage) {
    document.getElementById('moat-loading').style.display = 'none';
    document.getElementById('moat-content').style.display = 'none';
    document.getElementById('moat-initial').style.display = 'none';

    const errorElement = document.getElementById('moat-error');
    errorElement.style.display = 'block';
    errorElement.innerHTML = `
        <h6>🏰 MOAT Analysis Failed</h6>
        <p>${errorMessage}</p>
        <small class="text-muted">Please try again or contact support if the issue persists.</small>
    `;
}

function resetMOATAnalysis() {
    // Reset to initial state
    document.getElementById('moat-loading').style.display = 'none';
    document.getElementById('moat-content').style.display = 'none';
    document.getElementById('moat-error').style.display = 'none';
    document.getElementById('moat-initial').style.display = 'block';

    // Clear content
    document.getElementById('moat-executive-summary').innerHTML = '<p class="text-muted">Executive summary will appear here after analysis...</p>';
    document.getElementById('moat-analysis-content').innerHTML = '<p class="text-muted">MOAT analysis will appear here after analysis...</p>';
    document.getElementById('market-positioning-content').innerHTML = '<p class="text-muted">Market positioning analysis will appear here after analysis...</p>';
    document.getElementById('competitive-landscape-content').innerHTML = '<p class="text-muted">Competitive landscape analysis will appear here after analysis...</p>';

    // Reset title
    const mainTitle = document.querySelector('.col-lg-9 .card-panel h5');
    if (mainTitle) {
        mainTitle.innerHTML = '🏰 Competitive MOAT Analysis';
    }
}

// Manual tab switching function
function switchMOATTab(tabId) {
    console.log('🔄 Switching to tab:', tabId);

    // Hide all tab panes
    const allPanes = document.querySelectorAll('#moatTabContent .tab-pane');
    allPanes.forEach(pane => {
        pane.classList.remove('show', 'active');
    });

    // Remove active class from all tabs
    const allTabs = document.querySelectorAll('#moatTabs .nav-link');
    allTabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Show the selected tab pane
    const selectedPane = document.getElementById(tabId);
    if (selectedPane) {
        selectedPane.classList.add('show', 'active');
        console.log('✅ Activated pane:', tabId);
    }

    // Activate the corresponding tab button
    const selectedTab = document.querySelector(`#moatTabs button[data-bs-target="#${tabId}"]`);
    if (selectedTab) {
        selectedTab.classList.add('active');
        console.log('✅ Activated tab button');
    }
}

// Initialize manual tab handlers
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Setting up MOAT tabs...');

    // Add click handlers to each tab
    const tabs = [
        { buttonId: 'executive-tab', paneId: 'executive' },
        { buttonId: 'moat-tab', paneId: 'moat' },
        { buttonId: 'positioning-tab', paneId: 'positioning' },
        { buttonId: 'competitive-tab', paneId: 'competitive' }
    ];

    tabs.forEach(tab => {
        const button = document.getElementById(tab.buttonId);
        if (button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('🎯 Tab clicked:', tab.buttonId);
                switchMOATTab(tab.paneId);
            });
            console.log('✅ Added handler for:', tab.buttonId);
        } else {
            console.log('❌ Button not found:', tab.buttonId);
        }
    });

    console.log('✅ MOAT tabs initialized');
});

// ========================================
// MODIFY YOUR EXISTING SUBMIT FUNCTION
// ========================================

// Find your existing submit button event listener and replace it with this:
document.getElementById('submit').addEventListener('click', function() {
    const ticker = document.getElementById('ticker').value.trim().toUpperCase();

    if (!ticker) {
        alert('Please enter a stock ticker');
        return;
    }

    console.log(`📊 Starting analysis for ${ticker}...`);

    // Reset MOAT analysis first
    resetMOATAnalysis();

    // YOUR EXISTING STOCK DATA LOADING CODE GOES HERE
    // (Keep all your existing functionality - just add the MOAT analysis call)

    // Start MOAT analysis after a short delay
    setTimeout(() => {
        console.log(`🏰 Starting MOAT analysis for ${ticker}...`);
        runMOATAnalysis(ticker);
    }, 2000); // Start MOAT analysis 2 seconds after main data load
});

// ========================================
// HANDLE PERIOD CHANGES (1M, 3M, 6M, 1Y, 5Y)
// ========================================

// Add event listeners to period buttons to trigger MOAT analysis
document.addEventListener('DOMContentLoaded', function() {
    const periodButtons = document.querySelectorAll('input[name="period"]');

    periodButtons.forEach(button => {
        button.addEventListener('change', function() {
            const ticker = document.getElementById('ticker').value.trim().toUpperCase();

            if (ticker) {
                console.log(`📅 Period changed to ${this.value} for ${ticker}`);

                // Reset MOAT analysis
                resetMOATAnalysis();

                // YOUR EXISTING PERIOD CHANGE CODE GOES HERE
                // (Keep your existing chart update logic)

                // Restart MOAT analysis for new period
                setTimeout(() => {
                    console.log(`🏰 Restarting MOAT analysis for ${ticker} (${this.value} period)...`);
                    runMOATAnalysis(ticker);
                }, 1500);
            }
        });
    });
});

// ========================================
// AUTO-RUN ON PAGE LOAD (like your existing agent)
// ========================================

// Auto-run MOAT analysis when page loads (if ticker is pre-filled)
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for page to fully load
    setTimeout(() => {
        const ticker = document.getElementById('ticker').value.trim().toUpperCase();

        if (ticker) {
            console.log(`🚀 Auto-starting MOAT analysis for pre-filled ticker: ${ticker}`);

            // Wait for your existing stock analysis to start first
            setTimeout(() => {
                runMOATAnalysis(ticker);
            }, 3000); // 3 second delay to let main analysis start first
        }
    }, 1000);
});

document.addEventListener("DOMContentLoaded", function () {
    const subscribeBtn = document.getElementById("subscribe-button");
    if (subscribeBtn) {
        subscribeBtn.addEventListener("click", async function (e) {
            e.preventDefault();
            try {
                const res = await fetch("/create-checkout-session", {
                    method: "POST",
                });
                const data = await res.json();
                if (data.url) {
                    window.location.href = data.url;
                } else {
                    alert("Checkout failed: " + (data.error || "Unknown error"));
                }
            } catch (err) {
                console.error("Stripe checkout error:", err);
                alert("There was a problem creating the checkout session.");
            }
        });
    }
});