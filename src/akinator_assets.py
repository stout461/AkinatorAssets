from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import json
import plotly
import webbrowser
from threading import Timer
from flask_session import Session
from auth import oauth, auth0
from functools import wraps
import os
import sys
import traceback
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from run_watchlist_scriptv2 import main
from stock_agent import analyze_and_parse_stock
from db_utils import (
    fetch_latest_agent_output, insert_agent_output,
    fetch_latest_moat_analysis, insert_moat_analysis
)
from dotenv import load_dotenv
from pathlib import Path
import stripe
from moat_agent import run_moat_analysis_for_web
from stock_plotter import StockPlotter  # Import our new plotting class


load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def scheduled_watchlist_run():
    """Background task to update watchlist cache."""
    try:
        df = main(return_dataframe=True)
        df['last_updated'] = datetime.now(timezone('US/Central')).strftime('%Y-%m-%d %I:%M %p CST')
        df.to_json('watchlist_cache.json', orient='records')
        print("✅ Watchlist updated at 11:17 PM CST")
    except Exception as e:
        print(f"❌ Watchlist update failed: {e}")


def load_watchlist_cache():
    """Load cached watchlist data."""
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


def open_browser():
    """Open browser to localhost."""
    webbrowser.open_new('http://localhost:8080/')


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)

# Initialize OAuth
oauth.init_app(app)

# Initialize Stock Plotter
stock_plotter = StockPlotter()


# Authentication Routes
@app.route("/login")
def login():
    return render_template('login.html')


@app.route('/auth/login')
def auth_login():
    return auth0.authorize_redirect(redirect_uri=os.getenv("AUTH0_CALLBACK_URL"))


@app.route("/callback")
def callback():
    token = auth0.authorize_access_token()
    session["user"] = token["userinfo"]
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?"
        f"returnTo={url_for('index', _external=True)}&"
        f"client_id={os.getenv('AUTH0_CLIENT_ID')}"
    )


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user"])


# Payment Routes
@app.route("/success")
def success():
    return "✅ Payment successful!"


@app.route("/cancel")
def cancel():
    return "❌ Payment canceled."


@app.route("/create-checkout-session", methods=["POST"])
@requires_auth
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": os.getenv("STRIPE_PRICE_ID"),
                    "quantity": 1,
                }
            ],
            success_url=os.getenv("DOMAIN_URL") + "/success",
            cancel_url=os.getenv("DOMAIN_URL") + "/cancel",
            customer_email=session["user"]["email"],
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        print("❌ Stripe error:", e)
        return jsonify(error=str(e)), 500


# Analysis Routes
@app.route('/api/moat-analysis', methods=['POST'])
@requires_auth
def moat_analysis():
    """API endpoint for MOAT analysis v2"""
    try:
        data = request.get_json()

        if not data or 'ticker' not in data:
            return jsonify({
                'success': False,
                'error': 'Ticker is required'
            }), 400

        ticker = data['ticker'].strip().upper()

        if not ticker:
            return jsonify({
                'success': False,
                'error': 'Valid ticker is required'
            }), 400

        print(f"🏰 Running MOAT analysis for {ticker}...")

        # Check cache first
        cached = fetch_latest_moat_analysis(ticker)
        if cached:
            print(f"📦 Returning cached MOAT for {ticker}")
            return jsonify({
                'success': True,
                'data': {
                    'ticker': ticker,
                    'duration': cached['duration'],
                    'sections': cached['sections'],
                    'timestamp': cached.get('timestamp')
                },
                'error': None
            })

        # Run fresh analysis
        result = run_moat_analysis_for_web(ticker)

        if result['success']:
            print(f"✅ MOAT analysis completed for {ticker}")
            timestamp = datetime.now().isoformat()
            insert_moat_analysis(ticker, result["sections"], result["duration"])
            return jsonify({
                'success': True,
                'data': {
                    'ticker': result['ticker'],
                    'duration': result['duration'],
                    'sections': result['sections'],
                    'timestamp': timestamp
                },
                'error': None
            })
        else:
            print(f"❌ MOAT analysis failed for {ticker}: {result['error']}")
            return jsonify({
                'success': False,
                'data': None,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"💥 MOAT analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'data': None,
            'error': f'Analysis failed: {str(e)}'
        }), 500


@app.route('/api/moat-health', methods=['GET'])
@requires_auth
def moat_health():
    """Health check for MOAT analysis system"""
    try:
        from moat_agent import run_moat_analysis_for_web

        return jsonify({
            'status': 'healthy',
            'moat_system': 'operational',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'moat_system': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/analyze_stock', methods=['POST'])
@requires_auth
def analyze_stock_route():
    """Stock analysis endpoint using agent."""
    try:
        ticker = request.form.get('ticker', '').strip().upper()
        if not ticker:
            return jsonify(success=False, error="Please enter a valid ticker symbol"), 400

        print(f"📊 Running analysis for {ticker}...")

        # Check cache first
        cached = fetch_latest_agent_output(ticker)
        if cached:
            print(f"📦 Using cached analysis for {ticker}")
            return jsonify({
                "success": True,
                "data": {
                    "ticker": ticker,
                    "duration": cached.get("duration"),
                    "search_calls": cached.get("search_calls"),
                    "executive_summary": cached.get("executive_summary"),
                    "metrics": cached.get("metrics"),
                    "sections": cached.get("sections", {}),
                    "timestamp": cached.get("timestamp")
                },
                "error": None
            })

        # Run live analysis
        result = analyze_and_parse_stock(ticker, verbose=True)
        if not result.get('success'):
            return jsonify(success=False, error=result.get('error', 'Agent analysis failed')), 500

        # Cache and return result
        output = {
            "ticker": ticker,
            "duration": result['duration'],
            "search_calls": result['search_calls'],
            "executive_summary": result['executive_summary'],
            "sections": result['parsed_sections'],
            "metrics": result['metrics'],
            "timestamp": datetime.now().isoformat()
        }
        insert_agent_output(ticker, output)

        return jsonify({
            "success": True,
            "data": {
                "ticker": ticker,
                "duration": result['duration'],
                "search_calls": result['search_calls'],
                "executive_summary": result['executive_summary'],
                "metrics": result['metrics'],
                "sections": result['parsed_sections'],
                "timestamp": cached.get("timestamp")
            },
            "error": None
        })

    except Exception as e:
        print(f"❌ Error during analysis for {ticker}: {str(e)}")
        print(traceback.format_exc())
        return jsonify(success=False, error=f"Server error: {str(e)}"), 500


# Main Application Routes
@app.route('/')
@requires_auth
def index():
    """Main dashboard page."""
    table_data, columns, last_updated = load_watchlist_cache()
    return render_template('index.html', table_data=table_data, columns=columns, last_updated=last_updated)


@app.route('/run_watchlist', methods=['POST'])
@requires_auth
def run_watchlist():
    """Run watchlist analysis and cache results."""
    try:
        df = main(return_dataframe=True)

        # Cache DataFrame for reuse
        cache_path = os.path.join(os.getcwd(), 'watchlist_cache.json')
        df.to_json(cache_path, orient='records')

        table_data = df.to_dict(orient='records')
        columns = list(df.columns)

        return jsonify(success=True, table=table_data, columns=columns)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/plot', methods=['POST'])
@requires_auth
def plot():
    """
    Main endpoint to return Plotly chart and stock/financial data in JSON.
    Now uses the StockPlotter class for all plotting logic.
    """
    try:
        # Extract parameters from request
        ticker = request.form['ticker'].strip().upper()
        period = request.form.get('period', '1Y')
        chart_mode = request.form.get('chartMode', 'fib')
        manual_fib = request.form.get('manualFib', 'false') == 'true'

        if chart_mode == 'fib':
            manual_fib = request.form.get('manualFib', 'false') == 'true'

        show_extensions = request.form.get('showExtensions', 'false') == 'true'
        fib_high = request.form.get('fibHigh')
        show_fib = request.form.get('showFib', 'false') == 'true'  # New parameter

        # Handle moving averages
        moving_averages = []
        ma_periods_str = request.form.get('movingAverages', '')
        if ma_periods_str:
            try:
                # Parse comma-separated list of periods
                ma_periods = [int(x.strip()) for x in ma_periods_str.split(',') if x.strip()]
                moving_averages = [period for period in ma_periods if period > 0]
            except ValueError:
                print("Error parsing moving average periods, using defaults")
                moving_averages = []

        # Use StockPlotter to create the plot
        result = stock_plotter.create_stock_plot(
            ticker=ticker,
            period=period,
            chart_mode=chart_mode,
            manual_fib=manual_fib,
            show_extensions=show_extensions,
            fib_high=fib_high,
            moving_averages=moving_averages,
            show_fib=show_fib  # Pass the new parameter
        )

        # Convert figure to JSON
        graph_json = json.dumps(result['figure'], cls=plotly.utils.PlotlyJSONEncoder)

        # Return all data
        return jsonify(
            graph=graph_json,
            price=result['price_stats'],
            financials=result['financial_metrics'],
            priceTarget=result['price_target']
        )

    except ValueError as e:
        return jsonify(error=str(e))
    except Exception as e:
        print(f"Error in plot function: {str(e)}")
        return jsonify(error=f"An error occurred: {str(e)}")


# Application startup
if __name__ == '__main__':
    # Open browser after short delay
    Timer(1, open_browser).start()

    # Schedule background watchlist updates
    scheduler = BackgroundScheduler(timezone='US/Central')
    scheduler.add_job(scheduled_watchlist_run, 'cron', hour=16, minute=30)
    scheduler.start()

    # Run Flask app
    app.run(host='127.0.0.1', port=8080, debug=False)