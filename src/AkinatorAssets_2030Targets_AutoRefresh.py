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
import sys
import os
sys.path.append(os.getcwd())  # Assumes run_watchlist_scriptv2.py is in same dir
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from run_watchlist_scriptv2 import main
from schwab_api.client import SchwabClient
from schwab_api.auth import SchwabAuth

auth = SchwabAuth()
client = SchwabClient(auth)

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
    """Fetch historical OHLCV data from Schwab API."""
    try:
        # Convert start/end dates to epoch milliseconds
        # Ensure datetime format
        if isinstance(start_date, datetime):
            start_dt = start_date
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if isinstance(end_date, datetime):
            end_dt = end_date
        else:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Convert to epoch ms
        start_ms = int(time.mktime(start_dt.timetuple()) * 1000)
        end_ms = int(time.mktime(end_dt.timetuple()) * 1000)

        # Fetch price history
        data = client.get_price_history(
            symbol=symbol,
            start_date=start_ms,
            end_date=end_ms,
            period_type="year",       # explicitly allow daily data
            frequency_type="daily",   # daily candles
            frequency=1
        )


        candles = data.get("candles", [])
        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame(candles)
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        return df

    except Exception as e:
        print(f"Error getting Schwab price history for {symbol}: {e}")
        return pd.DataFrame()

def get_finance_data(symbol):
    """Fetch fundamental metrics from Schwab API."""
    try:
        result = client.search_instruments(symbol, projection="fundamental")
        instruments = result.get("instruments", [])
        if instruments:
            return instruments[0].get("fundamental", {})

    except Exception as e:
        print(f"Error fetching Schwab financial data for {symbol}: {e}")
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
    chart_mode = request.form.get('chartMode', 'fib')
    manual_fib = request.form.get('manualFib', 'false') == 'true' if chart_mode == 'fib' else False
    show_extensions = request.form.get('showExtensions', 'false') == 'true'
    fib_high = request.form.get('fibHigh')
    debug = True

    if not ticker:
        return jsonify(error="Please enter a valid ticker symbol")

    try:
        end_date = datetime.now()
        period_map = {
            '1M': 30, '3M': 90, '6M': 180, '1Y': 365, '5Y': 365*5
        }
        days = period_map.get(period, 365)
        start_date = end_date - timedelta(days=days)

        df = get_stock_data(ticker, start_date, end_date)
        if df.empty:
            return jsonify(error=f"No data found for ticker: {ticker}")

        fig = go.Figure()
        df.index = pd.to_datetime(df.index)
        x_dates = df.index.strftime('%Y-%m-%d').tolist()
        y_values = df['Close'].tolist()

        fig.add_trace(go.Scatter(
            x=x_dates,
            y=y_values,
            mode='lines',
            name='Close Price',
            line=dict(color='#0ac775', width=2)
        ))

        if chart_mode == 'fib' and manual_fib and fib_high:
            try:
                fib_high_val = float(fib_high)
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
                for level, value in fib_levels.items():
                    fig.add_trace(go.Scatter(
                        x=x_dates, y=[value]*len(x_dates), mode='lines',
                        line=dict(color=fib_colors.get(level), width=1, dash='dash'),
                        name=f"{level.upper()} - ${value:.2f}"
                    ))
                if show_extensions:
                    for ratio in [1.272, 1.382, 1.618, 2.618]:
                        ext_value = fib_high_val * ratio
                        fig.add_trace(go.Scatter(
                            x=x_dates, y=[ext_value]*len(x_dates), mode='lines',
                            line=dict(color='rgba(255,100,100,0.5)', width=1, dash='dash'),
                            name=f"{ratio*100:.1f}% - ${ext_value:.2f}"
                        ))
            except ValueError:
                if debug:
                    print("Invalid fib high")

        fig.update_layout(
            title=f"{ticker} Stock Price - {period}",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            template="plotly_white",
            height=600
        )

        financial_data = get_finance_data(ticker)
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
            "revenueGrowth": format_growth(financial_data.get('revChangeTTM')/100),
            "forwardPE": format_ratio(financial_data.get('pegRatio')),
            "trailingPE": format_ratio(financial_data.get('peRatio')),
            "profitMargin": format_growth(financial_data.get('netProfitMarginTTM')/100),
            "priceToSales": format_ratio(financial_data.get('prRatio')),
            "totalRevenue": format_revenue_billions(
                financial_data.get('marketCap') / financial_data.get('prRatio')
                if financial_data.get('marketCap') and financial_data.get('prRatio') else None
            ),
            "marketCap": format_revenue_billions(financial_data.get('marketCap')),
        }

        # Revenue estimation
        pr_ratio = financial_data.get("prRatio")
        market_cap = financial_data.get("marketCap")
        revenue = market_cap / pr_ratio if market_cap and pr_ratio else None

        revenue_growth = financial_data.get('revChangeTTM')
        if revenue_growth is not None:
            revenue_growth /= 100  # Schwab gives it in %

        trailing_pe = financial_data.get('peRatio')
        profit_margin = financial_data.get('netProfitMarginTTM')  # Already %

        future_value, rate_increase, adjustments = calculate_future_value(
            revenue, revenue_growth, market_cap, trailing_pe, profit_margin
        )
        price_target = {
            "futureValue": None if future_value is None else f"${future_value:.2f}B",
            "rateIncrease": None if rate_increase is None else f"{rate_increase:.2f}x",
            "adjustments": adjustments
        }

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return jsonify(graph=graphJSON, price=price_stats, financials=financial_metrics, priceTarget=price_target)

    except Exception as e:
        print(f"Error in plot function: {str(e)}")
        return jsonify(error=f"An error occurred: {str(e)}")


if __name__ == '__main__':
    Timer(1, open_browser).start()

    scheduler = BackgroundScheduler(timezone='US/Central')
    scheduler.add_job(scheduled_watchlist_run, 'cron', hour=16, minute=30)
    scheduler.start()

    app.run(host='0.0.0.0', port=5000, debug=False)

