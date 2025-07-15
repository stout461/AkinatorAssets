console.log("✅ script.js loaded");

let chartDataX = [];
let pointForLine = null;
let trendLineCount = 0;
let customMAs = [];

// ADD: Elliott Wave Support
let elliottPoints = [];

// ========================================
// UTILITY FUNCTIONS
// ========================================

function getChartClickMode() {
    return $('input[name="chartClickMode"]:checked').val();
}

function randomColor() {
    const colors = ['#FF5733', '#33FFCC', '#FF33A6', '#3371FF', '#FFD633', '#4CAF50'];
    return colors[Math.floor(Math.random() * colors.length)];
}

function getSelectedMovingAverages() {
    const selectedMAs = [];

    // Get checked standard MAs
    $('.ma-checkbox:checked').each(function() {
        selectedMAs.push(parseInt($(this).val()));
    });

    // Add custom MAs
    customMAs.forEach(function(period) {
        selectedMAs.push(period);
    });

    // Remove duplicates and sort
    return [...new Set(selectedMAs)].sort((a, b) => a - b);
}

// ADD: Elliott Wave Support
function updateElliottDisplay() {
    const list = $('#elliott-points-list');
    console.log('Updating Elliott display with points:', elliottPoints);
    list.empty();
    elliottPoints.forEach((p, i) => {
        list.append(`<li>Point ${i}: ${p.x} - $${p.y} <button class="remove-elliott-point btn btn-sm btn-danger" data-index="${i}">Remove</button></li>`);
    });
}

// ========================================
// FETCH FUNCTIONS
// ========================================

function getCommonFetchParams() {
    const ticker = $('#ticker').val().trim();
    const period = $('input[name="period"]:checked').val();
    const chartMode = getChartClickMode();
    const manualFib = (chartMode === 'fib') && $('#manualFibMode').is(':checked');
    const showExtensions = $('#showExtensions').is(':checked');
    const fibHigh = $('#fibHighValue').val();
    const selectedMAs = getSelectedMovingAverages();
    const movingAveragesParam = selectedMAs.length > 0 ? selectedMAs.join(',') : '';
    const showFib = $('#showFib').is(':checked');

    // ADD: Elliott Wave Support
    const elliottPointsParam = (chartMode === 'elliott' && elliottPoints.length > 0) ? JSON.stringify(elliottPoints) : '';

    return {
        ticker,
        period,
        chartMode,
        manualFib,
        showExtensions,
        fibHigh,
        movingAverages: movingAveragesParam,
        showFib,
        // ADD: Elliott Wave Support
        elliott_points: elliottPointsParam
    };
}

function fetchChartAndFinancials(onlyChart = false) {
    const params = getCommonFetchParams();

    if (!params.ticker) {
        $('#error').text('Please enter a valid ticker symbol').show();
        return Promise.reject('Invalid ticker');
    }

    // Show chart loading
    $('#loading').show();
    $('#error').hide();
    if (!onlyChart) {
        $('#stats-container').hide();
        $('#price-target-container').hide();
    }

    params.includeFinancials = onlyChart ? 'false' : 'true';  // New param to control backend fetch

    return $.ajax({
        url: '/plot',
        type: 'POST',
        data: params
    }).done(function(response) {
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

        // Update sections only if not onlyChart
        if (!onlyChart) {
            updatePriceStats(response);
            updateFinancialMetrics(response);
            initUserProjections(response);
            $('#stats-container').show();
            $('#price-target-container').show();
        }
    }).fail(function(error) {
        $('#loading').hide();
        $('#error').text('Chart request failed. Please try again.').show();
    });
}

function fetchAnalysis(forceRefresh = false) {
    const ticker = $('#ticker').val().trim();

    if (!ticker) {
        return Promise.reject('Invalid ticker');
    }

    // Show analysis loading
    $('#analysis-loading').show();
    $('#analysis-container').hide();
    $('#analysis-container .card-panel').removeClass('analysis-success');

    const data = { ticker };
    if (forceRefresh) {
        data.force_refresh = true;
    }

    return $.ajax({
        url: '/analyze_stock',
        type: 'POST',
        data: data
    }).done(function(response) {
        $('#analysis-loading').hide();

        if (response.success) {
            displayAnalysisResults(response);
            updateAnalysisTimestamp(response);
            setupAnalysisRefreshButton();
            $('#analysis-container').show();
            console.log(`✅ Analysis completed in ${response.duration}s with ${response.search_calls} searches`);
        } else {
            displayAnalysisError(response.error);
        }
    }).fail(function(error) {
        $('#analysis-loading').hide();
        displayAnalysisError('Analysis request failed. Please check your connection and try again.');
    });
}

function fetchMOATAnalysis(forceRefresh = false) {
    const ticker = $('#ticker').val().trim();

    if (!ticker) {
        return Promise.reject('Invalid ticker');
    }

    // Show MOAT loading
    showMOATLoading();

    const body = { ticker };
    if (forceRefresh) {
        body.force_refresh = true;
    }

    return fetch('/api/moat-analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
    })
    .then(response => response.json())
    .then(data => {
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

function loadAllData() {
    const params = getCommonFetchParams();

    if (!params.ticker) {
        $('#error').text('Please enter a valid ticker symbol').show();
        return;
    }

    // Reset all sections
    resetMOATAnalysis();
    $('#analysis-container').hide();
    $('#error').hide();

    // Fetch all in parallel
    Promise.all([
        fetchChartAndFinancials(),
        fetchAnalysis(),
        fetchMOATAnalysis()
    ]).then(() => {
        console.log('✅ All data loaded');
    }).catch(error => {
        console.error('Error loading data:', error);
    });
}

// ========================================
// DISPLAY AND UPDATE FUNCTIONS
// ========================================

// Split updateFinancialStats into two functions
function updatePriceStats(response) {
    $('#current-price').text(response.price.current);
    $('#period-change').text(response.price.change);
    $('#year-high').text(response.price.high);
    $('#year-low').text(response.price.low);
}

function updateFinancialMetrics(response) {
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

function displayAnalysisResults(response) {
    try {
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
        updateAnalysisTimestamp(response.data);
        console.log('✅ Analysis sections updated successfully');
    } catch (error) {
        console.error('Error formatting analysis results:', error);
        displayAnalysisError('Error formatting analysis results');
    }
}

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

function updateAnalysisTimestamp(data) {
    const timestampElement = document.getElementById('analysis-timestamp');
    if (data.timestamp) {
        const dbTimestamp = new Date(data.timestamp);
        const dateString = dbTimestamp.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        const timeString = dbTimestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        timestampElement.textContent = `Last updated: ${dateString} at ${timeString}`;
    }
}

function setupAnalysisRefreshButton() {
    const refreshBtn = document.getElementById('refresh-analysis-btn');
    if (refreshBtn) {
        refreshBtn.style.display = 'inline-block';
        refreshBtn.removeEventListener('click', handleAnalysisRefresh);
        refreshBtn.addEventListener('click', handleAnalysisRefresh);
    }
}

function handleAnalysisRefresh() {
    console.log(`🔄 Refreshing analysis for ${$('#ticker').val().trim()}...`);
    fetchAnalysis(true);
}

// ========================================
// MOAT FUNCTIONS
// ========================================

function showMOATLoading() {
    document.getElementById('moat-initial').style.display = 'none';
    document.getElementById('moat-content').style.display = 'none';
    document.getElementById('moat-error').style.display = 'none';
    document.getElementById('moat-loading').style.display = 'block';
}

function displayMOATAnalysis(data) {
    console.log('✅ Displaying MOAT analysis:', data);

    document.getElementById('moat-loading').style.display = 'none';
    document.getElementById('moat-error').style.display = 'none';
    document.getElementById('moat-initial').style.display = 'none';
    document.getElementById('moat-content').style.display = 'block';

    populateMOATSection('moat-executive-summary', data.sections.executive_summary);
    populateMOATSection('moat-analysis-content', data.sections.moat_analysis);
    populateMOATSection('market-positioning-content', data.sections.market_positioning);
    populateMOATSection('competitive-landscape-content', data.sections.competitive_landscape);
    updateMOATTimestamp();
    setupMOATRefreshButton();

    const mainTitle = document.querySelector('.col-lg-9 .card-panel h5');
    if (mainTitle && data.ticker) {
        mainTitle.innerHTML = `🏰 Competitive MOAT Analysis - ${data.ticker}`;
    }

    setTimeout(() => {
        switchMOATTab('executive');
    }, 500);
    updateMOATTimestamp(data);  // Pass the data object
    setupMOATRefreshButton();
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

    const formattedContent = formatMOATContent(content);
    element.innerHTML = formattedContent;
}

function formatMOATContent(content) {
    let formatted = content;
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/^- (.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/^• (.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    formatted = formatted.replace(/<\/ul>\s*<ul>/g, '');

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
    document.getElementById('moat-loading').style.display = 'none';
    document.getElementById('moat-content').style.display = 'none';
    document.getElementById('moat-error').style.display = 'none';
    document.getElementById('moat-initial').style.display = 'block';

    document.getElementById('moat-executive-summary').innerHTML = '<p class="text-muted">Executive summary will appear here after analysis...</p>';
    document.getElementById('moat-analysis-content').innerHTML = '<p class="text-muted">MOAT analysis will appear here after analysis...</p>';
    document.getElementById('market-positioning-content').innerHTML = '<p class="text-muted">Market positioning analysis will appear here after analysis...</p>';
    document.getElementById('competitive-landscape-content').innerHTML = '<p class="text-muted">Competitive landscape analysis will appear here after analysis...</p>';

    const mainTitle = document.querySelector('.col-lg-9 .card-panel h5');
    if (mainTitle) {
        mainTitle.innerHTML = '🏰 Competitive MOAT Analysis';
    }
}

function switchMOATTab(tabId) {
    console.log('🔄 Switching to tab:', tabId);

    const allPanes = document.querySelectorAll('#moatTabContent .tab-pane');
    allPanes.forEach(pane => {
        pane.classList.remove('show', 'active');
    });

    const allTabs = document.querySelectorAll('#moatTabs .nav-link');
    allTabs.forEach(tab => {
        tab.classList.remove('active');
    });

    const selectedPane = document.getElementById(tabId);
    if (selectedPane) {
        selectedPane.classList.add('show', 'active');
        console.log('✅ Activated pane:', tabId);
    }

    const selectedTab = document.querySelector(`#moatTabs button[data-bs-target="#${tabId}"]`);
    if (selectedTab) {
        selectedTab.classList.add('active');
        console.log('✅ Activated tab button');
    }
}

function updateMOATTimestamp(data) {
    const timestampElement = document.getElementById('moat-timestamp');
    if (timestampElement && data && data.timestamp) {
        const dbTimestamp = new Date(data.timestamp);
        const dateString = dbTimestamp.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        const timeString = dbTimestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        timestampElement.textContent = `Last updated: ${dateString} at ${timeString}`;
    }
}

function setupMOATRefreshButton() {
    const refreshBtn = document.getElementById('refresh-moat-btn');
    if (refreshBtn) {
        refreshBtn.style.display = 'inline-block';
        refreshBtn.removeEventListener('click', handleMOATRefresh);
        refreshBtn.addEventListener('click', handleMOATRefresh);
    }
}

function handleMOATRefresh() {
    console.log(`🔄 Refreshing MOAT analysis for ${$('#ticker').val().trim()}...`);
    fetchMOATAnalysis(true);
}

// ========================================
// CHART EVENT HANDLERS
// ========================================

function chartClickHandler(data) {
    const clickMode = getChartClickMode();
    const clickedY = data.points[0].y;

    if (clickMode === 'fib') {
        if ($('#manualFibMode').is(':checked')) {
            $('#fibHighValue').val(clickedY.toFixed(2));
            fetchChartAndFinancials();
        }
    } else if (clickMode === 'trendlines') {
        const mode = $('#trendLineMode').val();
        if (mode === 'off') return;

        let clickedX = data.points[0].x;
        if (mode === 'horizontal') {
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
    // ADD: Elliott Wave Support
    } else if (clickMode === 'elliott') {
        const clickedX = data.points[0].x;
        const clickedY = data.points[0].y.toFixed(2);
        elliottPoints.push({ x: clickedX, y: clickedY });
        updateElliottDisplay();
        fetchChartAndFinancials(true);  // Refresh chart only to show updates and projections
    }
}

// ========================================
// EVENT LISTENERS
// ========================================

$(document).ready(function() {
    // Watchlist table loading (unchanged)
    if (cachedData && cachedCols) {
        $('#watchlist-head').empty();
        $('#watchlist-body').empty();

        cachedCols.forEach(col => {
            $('#watchlist-head').append(`<th>${col}</th>`);
        });

        cachedData.forEach(row => {
            const rowHtml = cachedCols.map(col => {
                const cellValue = row[col] !== null ? row[col] : '';

                if (col === "5Y Multibagger Rate") {
                    const rate = parseFloat(cellValue);
                    let backgroundColor = "#ffffff";

                    if (!isNaN(rate)) {
                        const midpoint = 1.5;
                        let intensity;

                        if (rate < midpoint) {
                            intensity = Math.round(255 * (rate / midpoint));
                            backgroundColor = `rgb(255, ${intensity}, ${intensity})`;
                        } else {
                            const greenRange = Math.min(rate - midpoint, 3.5);
                            intensity = Math.round(255 * (1 - greenRange / 2));
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
            pageLength: 25,
            lengthMenu: [10, 25, 50, 100]
        });
    }

    // Chart click mode change
    $('input[name="chartClickMode"]').on('change', function() {
        const mode = getChartClickMode();
        if (mode === 'fib') {
            $('#fibSettings').show();
            $('#trendLineSettings').hide();
            // ADD: Elliott Wave Support
            $('#elliott-settings').hide();
        } else if (mode === 'trendlines') {
            $('#fibSettings').hide();
            $('#trendLineSettings').show();
            // ADD: Elliott Wave Support
            $('#elliott-settings').hide();
        // ADD: Elliott Wave Support
        } else if (mode === 'elliott') {
            $('#fibSettings').hide();
            $('#trendLineSettings').hide();
            $('#elliott-settings').show();
            updateElliottDisplay();  // Show current points if any
        }
    });

    // Fib toggles - only update chart
    $('#manualFibMode').on('change', function() {
        if (!$(this).is(':checked')) {
            $('#fibHighValue').val('');
        }
        if (getChartClickMode() === 'fib') {
            fetchChartAndFinancials(true);
        }
    });

    $('#showExtensions').on('change', function() {
        if (getChartClickMode() === 'fib') {
            fetchChartAndFinancials(true);
        }
    });

    $('#showFib').on('change', function() {
        if (getChartClickMode() === 'fib') {
            fetchChartAndFinancials(true);
        }
    });

    $('#fibHighValue').on('change', function() {
        if ($(this).val() && getChartClickMode() === 'fib') {
            fetchChartAndFinancials(true);
        }
    });

    // User projection sliders
    $('#user-revenue-growth, #user-profit-margin, #user-pe-ratio').on('input', calculateUserProjection);

    // MOAT tab handlers
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
                switchMOATTab(tab.paneId);
            });
        }
    });

    // Moving Averages UI
    $('#ma-preset-none').click(function() {
        $('.ma-checkbox').prop('checked', false);
        if ($('#auto-refresh-ma').is(':checked')) {
            fetchChartAndFinancials(true);
        }
    });

    $('#ma-preset-basic').click(function() {
        $('.ma-checkbox').prop('checked', false);
        $('#ma-20, #ma-50').prop('checked', true);
        if ($('#auto-refresh-ma').is(':checked')) {
            fetchChartAndFinancials(true);
        }
    });

    $('#ma-preset-extended').click(function() {
        $('.ma-checkbox').prop('checked', false);
        $('#ma-20, #ma-50, #ma-200').prop('checked', true);
        if ($('#auto-refresh-ma').is(':checked')) {
            fetchChartAndFinancials(true);
        }
    });

    $('#ma-preset-day-trading').click(function() {
        $('.ma-checkbox').prop('checked', false);
        $('#ma-5, #ma-10, #ma-20').prop('checked', true);
        if ($('#auto-refresh-ma').is(':checked')) {
            fetchChartAndFinancials(true);
        }
    });

    $('.ma-checkbox').change(function() {
        if ($('#auto-refresh-ma').is(':checked')) {
            fetchChartAndFinancials(true);
        }
    });

    $('#add-custom-ma').click(function() {
        const period = parseInt($('#custom-ma-input').val());
        if (period && period > 0 && period <= 500) {
            if (!customMAs.includes(period)) {
                customMAs.push(period);
                updateCustomMADisplay();
                $('#custom-ma-input').val('');
                if ($('#auto-refresh-ma').is(':checked')) {
                    fetchChartAndFinancials(true);
                }
            } else {
                alert('This moving average period is already added.');
            }
        } else {
            alert('Please enter a valid period between 1 and 500.');
        }
    });

    $('#custom-ma-input').keypress(function(e) {
        if (e.which === 13) {
            $('#add-custom-ma').click();
        }
    });

    function updateCustomMADisplay() {
        const customMAList = $('#custom-ma-list');
        customMAList.empty();

        if (customMAs.length === 0) {
            $('#custom-ma-display').hide();
            return;
        }

        $('#custom-ma-display').show();

        customMAs.forEach(function(period) {
            const tag = $(`
                <span class="custom-ma-tag">
                    MA${period}
                    <span class="remove-custom-ma" data-period="${period}">×</span>
                </span>
            `);
            customMAList.append(tag);
        });
    }

    $('#chart-settings-toggle').click(function() {
        $('#chart-settings').toggle();
        $(this).text($('#chart-settings').is(':visible') ? 'Hide Settings' : 'Settings');
    });

    $(document).on('click', '.remove-custom-ma', function() {
        const period = parseInt($(this).data('period'));
        customMAs = customMAs.filter(p => p !== period);
        updateCustomMADisplay();
        if ($('#auto-refresh-ma').is(':checked')) {
            fetchChartAndFinancials(true);
        }
    });

    // ADD: Elliott Wave Support - Remove point handler
    $(document).on('click', '.remove-elliott-point', function() {
        const index = $(this).data('index');
        elliottPoints.splice(index, 1);
        updateElliottDisplay();
        fetchChartAndFinancials(true);
    });

    // ADD: Elliott Wave Support - Clear points
    $('#clear-elliott-points').click(function() {
        elliottPoints = [];
        updateElliottDisplay();
        fetchChartAndFinancials(true);
    });

    // Ticker/period listeners for full load
    $('#submit').on('click', loadAllData);
    $('#ticker').on('keypress', function(e) {
        if (e.which === 13) loadAllData();
    });
    $('input[name="period"]').on('change', loadAllData);

    // Auto-trigger on load
    loadAllData();
});
