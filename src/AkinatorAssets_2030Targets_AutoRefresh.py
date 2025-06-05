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
from stock_agent import analyze_and_parse_stock
import traceback
from agent_cache import get_cached_agent_output, cache_agent_output

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



@app.route('/analyze_stock', methods=['POST'])
def analyze_stock_route():
    try:
        ticker = request.form['ticker'].strip().upper()
        if not ticker:
            return jsonify(success=False, error="Please enter a valid ticker symbol")

        print(f"🎯 Starting stock analysis for {ticker}")

        # 🧠 Try cache first
        cached = get_cached_agent_output(ticker)
        if cached:
            print(f"✅ Returning cached agent result for {ticker}")
            return jsonify(success=True, **cached)

        # 🧠 Otherwise, run agent
        result = analyze_and_parse_stock(ticker, verbose=True)

        if result['success']:
            print(f"✅ Analysis completed for {ticker}")
            # ⏺️ Save only what's needed
            output = {
                "ticker": ticker,
                "duration": result['duration'],
                "search_calls": result['search_calls'],
                "executive_summary": result['executive_summary'],
                "sections": result['parsed_sections'],
                "metrics": result['metrics']
            }
            cache_agent_output(ticker, output)
            return jsonify(success=True, **output)
        else:
            print(f"❌ Analysis failed for {ticker}: {result['error']}")
            return jsonify(success=False, error=result['error'])

    except Exception as e:
        error_msg = f"Server error during analysis: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return jsonify(success=False, error=error_msg)

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

    app.run(host='127.0.0.1', port=8080, debug=False)
