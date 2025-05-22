from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import plotly
import plotly.graph_objs as go
from datetime import datetime, timedelta
import webbrowser
from threading import Timer
import requests
import time
import random
import yfinance as yf
import sys
import os
sys.path.append(os.getcwd())  # Assumes run_watchlist_scriptv2.py is in same dir
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from run_watchlist_scriptv2 import main

def scheduled_watchlist_run():
    try:
        df = main(return_dataframe=True)
        df['last_updated'] = datetime.now(timezone('US/Central')).strftime('%Y-%m-%d %I:%M %p CST')
        df.to_json('watchlist_cache.json', orient='records')
        print("✅ Watchlist updated at 11:17 PM CST")
    except Exception as e:
        print(f"❌ Watchlist update failed: {e}")

def load_watchlist_cache():
    try:
        cache_path = os.path.join(os.getcwd(), 'watchlist_cache.json')
        if os.path.exists(cache_path):
            df = pd.read_json(cache_path, orient='records')
            table_data = df.drop(columns=['last_updated'], errors='ignore').to_dict(orient='records')
            columns = [col for col in df.columns if col != 'last_updated']
            last_updated = df['last_updated'].iloc[0] if 'last_updated' in df.columns else "N/A"
            return table_data, columns, last_updated
    except Exception as e:
        print(f"Error loading cache: {e}")
    return None, None, "N/A"




app = Flask(__name__)

def format_growth(value):
    """Convert value to percentage format"""
    if value is None:
        return "N/A"
    try:
        return f"{float(value) * 100:.2f}%"
    except (ValueError, TypeError):
        return "N/A"

def format_ratio(value):
    """Format ratio to 2 decimal places"""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "N/A"

def format_revenue_billions(value):
    """Convert revenue to billions ($B)"""
    if value is None:
        return "N/A"
    try:
        return f"${float(value) / 1e9:.2f}B"
    except (ValueError, TypeError):
        return "N/A"

def get_stock_data(symbol, start_date, end_date):
    """Fetch historical data from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        if not df.empty and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.dropna()
        return df
    except Exception as e:
        print(f"Error getting data for {symbol}: {str(e)}")
        return pd.DataFrame()

def get_yfinance_data(symbol):
    """Fetch financial metrics from yfinance."""
    try:
        print(f"Getting yfinance data for {symbol}...")
        time.sleep(random.uniform(1, 3))  # Slight random delay

        stock = yf.Ticker(symbol)
        info = stock.info

        data = {
            'totalRevenue': info.get('totalRevenue', None),
            'revenueGrowth': info.get('revenueGrowth', None),
            'marketCap': info.get('marketCap', None),
            'trailingPE': info.get('trailingPE', None),
            'forwardPE': info.get('forwardPE', None),
            'profitMargins': info.get('profitMargins', None),
            'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months', None)
        }
        return data
    except Exception as e:
        print(f"Error with yfinance for {symbol}: {str(e)}")
        return {}

def calculate_future_value(revenue, revenue_growth, market_cap, trailing_pe, profit_margin):
    """Calculate a naive 5-year future value with mild data cleaning."""
    adjustments = []

    def trailing_pe_str(pe_val):
        return "N/A" if pe_val is None else f"{pe_val:.1f}"
    def profit_margin_str(pm_val):
        return "N/A" if pm_val is None else f"{pm_val:.1f}%"

    if revenue is None or revenue_growth is None or market_cap is None or market_cap == 0:
        return None, None, ""

    # Adjust revenue growth
    if revenue_growth <= 0:
        adjustments.append("Revenue growth adjusted to 5% from non-positive value")
        revenue_growth = 0.05
    elif revenue_growth > 0.25:
        adjustments.append(f"Revenue growth capped at 25% from {revenue_growth * 100:.1f}%")
        revenue_growth = 0.25

    # Adjust trailing P/E
    if trailing_pe is None or trailing_pe == 0 or trailing_pe > 30:
        old_pe_formatted = trailing_pe_str(trailing_pe)
        adjustments.append(f"P/E adjusted to 30 from {old_pe_formatted}")
        trailing_pe = 30

    # Adjust profit margin
    if profit_margin is None or profit_margin < 1:
        old_pm_formatted = profit_margin_str(profit_margin)
        adjustments.append(f"Profit margin adjusted to 5% from {old_pm_formatted}")
        profit_margin = 5

    profit_margin /= 100.0  # convert from percent to decimal

    future_value = revenue * ((1 + revenue_growth) ** 5) * profit_margin * trailing_pe
    future_value_billion = round(future_value / 1e9, 2)
    rate_increase = round(future_value / market_cap, 2)

    adjustment_explanation = "; ".join(adjustments)
    return future_value_billion, rate_increase, adjustment_explanation

def open_browser():
    webbrowser.open_new('http://localhost:8080/')

@app.route('/')
def index():
    table_data, columns, last_updated = load_watchlist_cache()
    return render_template('index.html', table_data=table_data, columns=columns, last_updated=last_updated)


@app.route('/run_watchlist', methods=['POST'])
def run_watchlist():
    try:
        # ✅ Use local main() function, not watchlist_main
        df = main(return_dataframe=True)

        # Cache DataFrame as JSON for reuse on startup
        cache_path = os.path.join(os.getcwd(), 'watchlist_cache.json')
        df.to_json(cache_path, orient='records')

        table_data = df.to_dict(orient='records')
        columns = list(df.columns)

        return jsonify(success=True, table=table_data, columns=columns)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/plot', methods=['POST'])
def plot():
    """
    Main endpoint to return the Plotly chart and stock/financial data in JSON
    """
    ticker = request.form['ticker'].strip().upper()
    period = request.form.get('period', '1Y')

    # If the user is in "Fibonacci" mode, we respect the "manualFib" checkbox.
    # If in "Trendline" mode, we do not draw the fib lines.
    # So let's interpret request.form for these booleans:
    chart_mode = request.form.get('chartMode', 'fib')   # "fib" or "trendlines"
    manual_fib = False
    if chart_mode == 'fib':  # only if they're in fib mode do we read the checkbox
        manual_fib = request.form.get('manualFib', 'false') == 'true'

    show_extensions = request.form.get('showExtensions', 'false') == 'true'
    fib_high = request.form.get('fibHigh')
    debug = True

    if not ticker:
        return jsonify(error="Please enter a valid ticker symbol")

    try:
        # Determine start/end date from period
        end_date = datetime.now()
        if period == '1M':
            start_date = end_date - timedelta(days=30)
        elif period == '3M':
            start_date = end_date - timedelta(days=90)
        elif period == '6M':
            start_date = end_date - timedelta(days=180)
        elif period == '1Y':
            start_date = end_date - timedelta(days=365)
        elif period == '5Y':
            start_date = end_date - timedelta(days=365*5)
        else:
            start_date = end_date - timedelta(days=365)

        df = get_stock_data(ticker, start_date, end_date)
        if df.empty:
            return jsonify(error=f"No data found for ticker: {ticker}")

        # Build the Plotly figure
        fig = go.Figure()

        # Convert index to datetime if needed
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        x_dates = df.index.strftime('%Y-%m-%d').tolist()
        y_values = df['Close'].tolist()

        # Price trace
        fig.add_trace(go.Scatter(
            x=x_dates,
            y=y_values,
            mode='lines',
            name='Close Price',
            line=dict(color='#0ac775', width=2)
        ))

        # Only draw Fibonacci lines if user selected "Fib" mode AND manualFib is true
        if chart_mode == 'fib' and manual_fib and fib_high:
            try:
                fib_high_val = float(fib_high)

                # Standard retracement levels
                fib_levels = {
                    'level0': fib_high_val,
                    'level236': fib_high_val * (1 - 0.236),
                    'level382': fib_high_val * (1 - 0.382),
                    'level50': fib_high_val * (1 - 0.5),
                    'level618': fib_high_val * (1 - 0.618),
                    'level786': fib_high_val * (1 - 0.786),
                }

                fib_colors = {
                    'level0': 'rgba(255, 0, 0, 0.7)',
                    'level236': 'rgba(255, 165, 0, 0.7)',
                    'level382': 'rgba(255, 255, 0, 0.7)',
                    'level50': 'rgba(0, 128, 0, 0.7)',
                    'level618': 'rgba(0, 0, 255, 0.7)',
                    'level786': 'rgba(128, 0, 128, 0.7)'
                }

                fib_names = {
                    'level0': '0% - ' + f"${fib_high_val:.2f}",
                    'level236': '23.6% - ' + f"${fib_levels['level236']:.2f}",
                    'level382': '38.2% - ' + f"${fib_levels['level382']:.2f}",
                    'level50': '50% - ' + f"${fib_levels['level50']:.2f}",
                    'level618': '61.8% - ' + f"${fib_levels['level618']:.2f}",
                    'level786': '78.6% - ' + f"${fib_levels['level786']:.2f}",
                }

                for level, value in fib_levels.items():
                    fig.add_trace(go.Scatter(
                        x=x_dates,
                        y=[value]*len(x_dates),
                        mode='lines',
                        line=dict(
                            color=fib_colors.get(level, 'rgba(128, 128, 128, 0.7)'),
                            width=1,
                            dash='dash'
                        ),
                        name=fib_names.get(level, level),
                        hoverinfo='name+y'
                    ))

                # Optional extension lines above fib_high
                if show_extensions:
                    ext_ratios = [1.272, 1.382, 1.618, 2.618]
                    ext_colors = ['#FF6666', '#FF8888', '#FFAAAA', '#FFC0CB']
                    for i, ratio in enumerate(ext_ratios):
                        extension_value = fib_high_val * ratio
                        ratio_percent = ratio * 100
                        fig.add_trace(go.Scatter(
                            x=x_dates,
                            y=[extension_value]*len(x_dates),
                            mode='lines',
                            line=dict(
                                color=ext_colors[i],
                                width=1,
                                dash='dash'
                            ),
                            name=f"{ratio_percent:.1f}% - ${extension_value:.2f}",
                            hoverinfo='name+y'
                        ))
            except ValueError:
                if debug:
                    print("Error: Could not parse the manual fib high value.")

        # Layout
        period_name = {
            "1M": "Past Month",
            "3M": "Past 3 Months",
            "6M": "Past 6 Months",
            "1Y": "Past Year",
            "5Y": "Past 5 Years"
        }.get(period, "Past Year")

        fig.update_layout(
            title=f"{ticker} Stock Price - {period_name}",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            template="plotly_white",
            height=600
        )

        # Get financial metrics
        financial_data = get_yfinance_data(ticker)

        current_price = df['Close'].iloc[-1]
        first_price = df['Close'].iloc[0]
        period_change = ((current_price / first_price) - 1) * 100
        high_price = df['High'].max()
        low_price = df['Low'].min()

        price_stats = {
            "current": f"${current_price:.2f}",
            "change": f"{period_change:.2f}%",
            "high": f"${high_price:.2f}",
            "low": f"${low_price:.2f}"
        }

        financial_metrics = {
            "revenueGrowth": format_growth(financial_data.get('revenueGrowth')),
            "forwardPE": format_ratio(financial_data.get('forwardPE')),
            "trailingPE": format_ratio(financial_data.get('trailingPE')),
            "profitMargin": format_growth(financial_data.get('profitMargins')),
            "priceToSales": format_ratio(financial_data.get('priceToSalesTrailing12Months')),
            "totalRevenue": format_revenue_billions(financial_data.get('totalRevenue')),
            "marketCap": format_revenue_billions(financial_data.get('marketCap'))
        }

        # Calculate naive 5-year price target
        revenue = financial_data.get('totalRevenue')
        revenue_growth = financial_data.get('revenueGrowth')
        market_cap = financial_data.get('marketCap')
        trailing_pe = financial_data.get('trailingPE')
        profit_margin = financial_data.get('profitMargins')
        if profit_margin is not None:
            profit_margin *= 100

        future_value, rate_increase, adjustments = calculate_future_value(
            revenue, revenue_growth, market_cap, trailing_pe, profit_margin
        )

        price_target = {
            "futureValue": None if future_value is None else f"${future_value}B",
            "rateIncrease": None if rate_increase is None else f"{rate_increase}x",
            "adjustments": adjustments
        }

        # Convert figure to JSON
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Return everything as JSON
        return jsonify(
            graph=graphJSON,
            price=price_stats,
            financials=financial_metrics,
            priceTarget=price_target
        )

    except Exception as e:
        print(f"Error in plot function: {str(e)}")
        return jsonify(error=f"An error occurred: {str(e)}")


if __name__ == '__main__':
    Timer(1, open_browser).start()

    scheduler = BackgroundScheduler(timezone='US/Central')
    scheduler.add_job(scheduled_watchlist_run, 'cron', hour=16, minute=30)
    scheduler.start()

    app.run(host='0.0.0.0', port=8080, debug=False)

    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # -- The HTML Template below includes a "Chart Click Mode" radio group:
    #    - Fibonacci
    #    - Trendlines
    #    We then only set fibHighValue from clicks if chartMode=fib,
    #    or draw lines if chartMode=trendlines.
    with open('templates/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Akinator Assets</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #f4f8f7;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .container-fluid {
            width: 100%;
            padding: 20px 40px;
        }
        h1 {
            color: #0ac775;
        }
        .card-panel {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .fib-settings, #trendLineSettings {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .fib-label {
            display: inline-block;
            margin-right: 10px;
            font-weight: 500;
        }
        .stat-label {
            color: #555;
            font-weight: 500;
        }
        .stat-value {
            font-weight: 600;
            color: #333;
        }
        #graph {
            width: 100%;
        }
        .form-check-input:checked {
            background-color: #0ac775;
            border-color: #0ac775;
        }
        .spinner-border.text-primary {
            color: #0ac775 !important;
        }
        .text-primary {
            color: #0ac775 !important;
        }
        .btn-primary {
            background-color: #0ac775;
            border-color: #0ac775;
        }
        .btn-primary:hover {
            background-color: #0cbf72;
            border-color: #0cbf72;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="d-flex align-items-stretch mb-4" style="gap: 20px;">
    <!-- Logo Panel -->
    <div class="card-panel d-flex align-items-center justify-content-center" style="width: 160px; flex-shrink: 0;">
            <img src="{{ url_for('static', filename='akinator_logo.png') }}" alt="Akinator Assets Logo" style="max-height: 90px; max-width: 100%;">
    </div>

    <!-- Ticker + Period Selection Panel -->
    <div class="card-panel flex-grow-1">
            <div class="input-group mb-3">
                <input type="text" id="ticker" class="form-control" placeholder="Enter Stock Ticker (e.g., AAPL)" value="AAPL">
                <button id="submit" class="btn btn-primary">Show Data</button>
            </div>
            <div class="btn-group w-100 mb-3" role="group">
                <input type="radio" class="btn-check" name="period" id="period1M" value="1M" autocomplete="off">
                <label class="btn btn-outline-secondary" for="period1M">1M</label>
    
                <input type="radio" class="btn-check" name="period" id="period3M" value="3M" autocomplete="off">
                <label class="btn btn-outline-secondary" for="period3M">3M</label>
    
                <input type="radio" class="btn-check" name="period" id="period6M" value="6M" autocomplete="off">
                <label class="btn btn-outline-secondary" for="period6M">6M</label>
    
                <input type="radio" class="btn-check" name="period" id="period1Y" value="1Y" autocomplete="off" checked>
                <label class="btn btn-outline-secondary" for="period1Y">1Y</label>
    
                <input type="radio" class="btn-check" name="period" id="period5Y" value="5Y" autocomplete="off">
                <label class="btn btn-outline-secondary" for="period5Y">5Y</label>
            </div>
        </div>
    </div>


        <!-- Stats Container (Price Info & Financials) -->
        <div id="stats-container" style="display:none;">
            <div class="card-panel">
                <h5 class="mb-3">Price Information</h5>
                <div class="row">
                    <div class="col-sm-3">
                        <p><span class="stat-label">Current Price:</span> <span id="current-price" class="stat-value"></span></p>
                    </div>
                    <div class="col-sm-3">
                        <p><span class="stat-label">Period Change:</span> <span id="period-change" class="stat-value"></span></p>
                    </div>
                    <div class="col-sm-3">
                        <p><span class="stat-label">Period High:</span> <span id="year-high" class="stat-value"></span></p>
                    </div>
                    <div class="col-sm-3">
                        <p><span class="stat-label">Period Low:</span> <span id="year-low" class="stat-value"></span></p>
                    </div>
                </div>
            </div>

            <div class="card-panel">
                <h5 class="mb-3">Financial Metrics</h5>
                <table class="table">
                    <tr>
                        <td class="stat-label">Revenue Growth:</td>
                        <td id="revenue-growth" class="stat-value"></td>
                    </tr>
                    <tr>
                        <td class="stat-label">Forward P/E:</td>
                        <td id="forward-pe" class="stat-value"></td>
                    </tr>
                    <tr>
                        <td class="stat-label">Trailing P/E:</td>
                        <td id="trailing-pe" class="stat-value"></td>
                    </tr>
                    <tr>
                        <td class="stat-label">Profit Margin:</td>
                        <td id="profit-margin" class="stat-value"></td>
                    </tr>
                    <tr>
                        <td class="stat-label">P/S Ratio:</td>
                        <td id="price-to-sales" class="stat-value"></td>
                    </tr>
                    <tr>
                        <td class="stat-label">Total Revenue:</td>
                        <td id="total-revenue" class="stat-value"></td>
                    </tr>
                    <tr>
                        <td class="stat-label">Market Cap:</td>
                        <td id="market-cap" class="stat-value"></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Loading & Error -->
        <div id="loading" class="text-center" style="display:none;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Fetching stock data...</p>
        </div>
        <div id="error" class="alert alert-danger" style="display:none;"></div>

        <!-- Price Target Container (User Projections) -->
        <div id="price-target-container" style="display:none;">
            <div class="card-panel price-target-card">
                <h5 class="mb-3">5-Year Price Target</h5>
                <table class="table">
                    <tr>
                        <td class="stat-label">Projected Future Value:</td>
                        <td id="future-value" class="stat-value">Loading...</td>
                    </tr>
                    <tr>
                        <td class="stat-label">Growth Potential:</td>
                        <td id="rate-increase" class="stat-value">Loading...</td>
                    </tr>
                </table>
                <div id="adjustment-note" class="text-muted" style="font-style: italic;"></div>

                <div class="mt-3">
                    <h6>Adjust Projections</h6>
                    <div class="mb-2">
                        <label for="user-revenue-growth" class="form-label">Revenue Growth (%)</label>
                        <input type="range" class="form-range" id="user-revenue-growth" min="0" max="40" step="0.5" value="5">
                        <div class="d-flex justify-content-between">
                            <small>0%</small>
                            <small id="user-revenue-growth-value">5%</small>
                            <small>40%</small>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label for="user-profit-margin" class="form-label">Profit Margin (%)</label>
                        <input type="range" class="form-range" id="user-profit-margin" min="1" max="60" step="0.5" value="10">
                        <div class="d-flex justify-content-between">
                            <small>1%</small>
                            <small id="user-profit-margin-value">10%</small>
                            <small>60%</small>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label for="user-pe-ratio" class="form-label">Projected P/E Ratio</label>
                        <input type="range" class="form-range" id="user-pe-ratio" min="5" max="50" step="1" value="20">
                        <div class="d-flex justify-content-between">
                            <small>5</small>
                            <small id="user-pe-ratio-value">20</small>
                            <small>50</small>
                        </div>
                    </div>
                    <div class="mt-3 p-2" style="background-color: #f0fff9; border-left: 3px solid #0ac775; border-radius: 4px;">
                        <h6>User Projection</h6>
                        <table class="table">
                            <tr>
                                <td class="stat-label">Projected Value:</td>
                                <td id="user-future-value" class="stat-value">-</td>
                            </tr>
                            <tr>
                                <td class="stat-label">Growth Potential:</td>
                                <td id="user-rate-increase" class="stat-value">-</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Chart Click Mode (Fib vs. Trendlines) -->
        <div class="card-panel">
            <label class="fib-label">Chart Click Mode:</label>
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="chartClickMode" id="modeFib" value="fib" checked>
                <label class="form-check-label" for="modeFib">Fibonacci</label>
            </div>
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="chartClickMode" id="modeTrendlines" value="trendlines">
                <label class="form-check-label" for="modeTrendlines">Trendlines</label>
            </div>
        </div>

        <!-- Fibonacci Settings -->
        <div class="fib-settings" id="fibSettings">
            <div class="form-check form-switch mb-2">
                <input class="form-check-input" type="checkbox" id="manualFibMode">
                <label class="form-check-label fib-label" for="manualFibMode">Manual Fibonacci High</label>
                <input type="number" class="form-control" id="fibHighValue" step="0.01" style="max-width:120px; display:inline-block;" placeholder="High" />
            </div>
            <div class="form-check form-switch mb-2">
                <input class="form-check-input" type="checkbox" id="showExtensions">
                <label class="form-check-label fib-label" for="showExtensions">Show Extensions</label>
            </div>
            <small class="text-muted">Click on the chart to set or enter values manually</small>
        </div>

        <!-- Trend Line Settings -->
        <div id="trendLineSettings" class="fib-settings" style="display:none;">
            <label for="trendLineMode" class="fib-label">Trend Lines Mode:</label>
            <select id="trendLineMode" class="form-select" style="max-width:180px; display:inline-block;">
                <option value="off" selected>Off</option>
                <option value="point">Point-to-Point</option>
                <option value="horizontal">Horizontal</option>
            </select>
            <small class="text-muted ms-2">Click on the chart to draw lines</small>
        </div>

        <!-- Chart Panel -->
        <div class="card-panel" id="graph-panel">
            <div id="graph"></div>
        </div>
    </div>

    <script>
        let chartDataX = [];
        let pointForLine = null;
        let trendLineCount = 0;

        // Ticker/period listeners
        $('#submit').on('click', fetchStockData);
        $('#ticker').on('keypress', function(e){ if(e.which === 13) fetchStockData(); });
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
        $(document).ready(function () {
            // Existing logic for loading watchlist table
            const cachedData = {{ table_data | tojson }};
            const cachedCols = {{ columns | tojson }};
            if (cachedData && cachedCols) {
                $('#watchlist-head').empty();
                $('#watchlist-body').empty();
        
                cachedCols.forEach(col => {
                    $('#watchlist-head').append(`<th>${col}</th>`);
                });
        
                cachedData.forEach(row => {
                    const rowHtml = cachedCols.map(col => `<td>${row[col] !== null ? row[col] : ''}</td>`).join('');
                    $('#watchlist-body').append(`<tr>${rowHtml}</tr>`);
                });
        
                $('#watchlist-table-container').show();
        
                if ($.fn.DataTable.isDataTable('#watchlist-table')) {
                    $('#watchlist-table').DataTable().destroy();
                }
                $('#watchlist-table').DataTable();
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
                    const xEnd   = chartDataX[chartDataX.length - 1];

                    const trace = {
                        x: [xStart, xEnd],
                        y: [clickedY, clickedY],
                        mode: 'lines',
                        line: { color: randomColor(), width: 2, dash: 'dot' },
                        name: 'H-Line ' + trendLineCount,
                        hoverinfo: 'none'
                    };
                    Plotly.addTraces('graph', trace);

                } else if (mode === 'point') {
                    // point-to-point line
                    if (!pointForLine) {
                        pointForLine = { x: clickedX, y: clickedY };
                    } else {
                        trendLineCount++;
                        const trace = {
                            x: [pointForLine.x, clickedX],
                            y: [pointForLine.y, clickedY],
                            mode: 'lines',
                            line: { color: randomColor(), width: 2 },
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
                const g = parseFloat(response.financials.revenueGrowth.replace('%',''));
                if (!isNaN(g)) $('#user-revenue-growth').val(Math.max(0, Math.min(40, g)));
            }
            if (response.financials.profitMargin !== 'N/A') {
                const pm = parseFloat(response.financials.profitMargin.replace('%',''));
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
    </script>
    
    <!-- Watchlist Table -->
    <div class="card-panel mt-4" id="watchlist-table-container" style="display:none;">
        <h5 class="mb-3">
            Watchlist Projections
            <small class="text-muted" style="font-size: 0.8em;">(Last updated: {{ last_updated }})</small>
        </h5>
        <div class="table-responsive">
            <table class="table table-striped" id="watchlist-table">
                <thead>
                    <tr id="watchlist-head"></tr>
                </thead>
                <tbody id="watchlist-body"></tbody>
            </table>
        </div>
    </div>
    
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css" />
</body>
</html>
''')

    app.run(host='0.0.0.0', port=8080, debug=False)
