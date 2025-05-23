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
    $('#loading').show();
    $('#error').hide();
    $('#stats-container').hide();
    $('#price-target-container').hide();

    // We'll decide "manualFib" = true if in fib mode AND manualFibMode is checked
    const chartMode = getChartClickMode();
    const manualFib = (chartMode === 'fib') && $('#manualFibMode').is(':checked');
    const showExtensions = $('#showExtensions').is(':checked');
    const fibHigh = $('#fibHighValue').val();

    $.ajax({
        url: '/plot',
        type: 'POST',
        data: {
            ticker: ticker,
            period: period,
            chartMode: chartMode,
            manualFib: manualFib,
            showExtensions: showExtensions,
            fibHigh: fibHigh
        },
        success: function(response) {
            $('#loading').hide();
            if (response.error) {
                $('#error').text(response.error).show();
                return;
            }
            // Plot the returned figure
            const figData = JSON.parse(response.graph);
            Plotly.newPlot('graph', figData.data, figData.layout).then(function() {
                var graphDiv = document.getElementById('graph');
                graphDiv.on('plotly_click', chartClickHandler);

                // store x-data in chartDataX for horizontal lines
                if (figData.data.length > 0) {
                    chartDataX = figData.data[0].x || [];
                }
            });

            // Update stats
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

            $('#stats-container').show();
            $('#price-target-container').show();
            initUserProjections(response);
        },
        error: function(error) {
            $('#loading').hide();
            $('#error').text('An error occurred while fetching data.').show();
        }
    });
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