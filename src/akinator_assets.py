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
        cache_path = os.path.join(os.path.dirname(__file__), 'watchlist_cache.json')
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
    """
    API endpoint for MOAT analysis v2 with force refresh capability
    Expects: {"ticker": "AAPL", "force_refresh": false}
    Returns: {"success": bool, "data": {...}, "error": str}
    """
    try:
        data = request.get_json()

        if not data or 'ticker' not in data:
            return jsonify({
                'success': False,
                'error': 'Ticker is required'
            }), 400

        ticker = data['ticker'].strip().upper()
        force_refresh = data.get('force_refresh', False)

        if not ticker:
            return jsonify({
                'success': False,
                'error': 'Valid ticker is required'
            }), 400

        print(f"🏰 Running MOAT analysis for {ticker} (force_refresh: {force_refresh})...")

        # Run MOAT analysis - check cache only if not forcing refresh
        if not force_refresh:
            cached = fetch_latest_moat_analysis(ticker)
            if cached:
                print(f"📦 Returning cached MOAT for {ticker}")
                return jsonify({
                    'success': True,
                    'data': {
                        'ticker': ticker,
                        'duration': cached['duration'],
                        'sections': cached['sections'],
                        'timestamp': cached.get('timestamp'),
                        'is_cached': True
                    },
                    'error': None
                })

        # Run fresh analysis
        print(f"🔄 Running fresh MOAT analysis for {ticker}...")
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
                    'timestamp': timestamp,
                    'is_cached': False
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
    try:
        ticker = request.form.get('ticker', '').strip().upper()
        force_refresh = request.form.get('force_refresh', 'false').lower() == 'true'

        if not ticker:
            return jsonify(success=False, error="Please enter a valid ticker symbol"), 400

        print(f"📊 Running analysis for {ticker} (force_refresh: {force_refresh})...")

        # Step 1: Try cache only if not forcing refresh
        if not force_refresh:
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
                        "timestamp": cached.get("timestamp"),
                        "is_cached": True
                    },
                    "error": None
                })

        # Step 2: Run live agent analysis
        print(f"🔄 Running fresh analysis for {ticker}...")
        result = analyze_and_parse_stock(ticker, verbose=True)
        if not result.get('success'):
            return jsonify(success=False, error=result.get('error', 'Agent analysis failed')), 500

        # Step 3: Store result in database
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

        # Step 4: Immediately retrieve from database to ensure consistent formatting
        cached = fetch_latest_agent_output(ticker)
        if not cached:
            return jsonify(success=False, error="Failed to retrieve stored analysis"), 500

        return jsonify({
            "success": True,
            "data": {
                "ticker": ticker,
                "duration": cached.get("duration"),
                "search_calls": cached.get("search_calls"),
                "executive_summary": cached.get("executive_summary"),
                "metrics": cached.get("metrics"),
                "sections": cached.get("sections", {}),
                "timestamp": cached.get("timestamp"),
                "is_cached": False
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


@app.route('/chart-preview')
def chart_preview():
    """Preview the chart component (temporary route for development)"""
    return render_template('chart_preview.html')


@app.route('/detailed-graph/<ticker>')
@requires_auth
def detailed_graph(ticker):
    """Detailed graph page for full-screen chart view"""
    period = request.args.get('period', '1Y')
    return render_template('detailed_graph.html', ticker=ticker, period=period)


@app.route('/run_watchlist', methods=['POST'])
@requires_auth
def run_watchlist():
    """Run watchlist analysis and cache results."""
    try:
        df = main(return_dataframe=True)

        # Cache DataFrame for reuse
        cache_path = os.path.join(os.path.dirname(__file__), 'watchlist_cache.json')
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
    Now uses the StockPlotter class for all plotting logic with unified subplot configuration support.
    
    Enhanced to support:
    - Unified subplot configuration format
    - Request validation for subplot configuration structure
    - Enhanced response format with layout metadata
    - Error handling with conflict information and suggestions
    """
    print("DEBUG: /plot endpoint hit")
    try:
        # Extract and validate basic parameters
        ticker = request.form.get('ticker', '').strip().upper()
        if not ticker:
            return jsonify(
                error="Ticker symbol is required",
                validation_errors=[{"field": "ticker", "message": "Ticker symbol cannot be empty"}]
            ), 400

        period = request.form.get('period', '1Y')
        chart_mode = request.form.get('chartMode', 'fib')
        manual_fib = request.form.get('manualFib', 'false') == 'true'

        if chart_mode == 'fib':
            manual_fib = request.form.get('manualFib', 'false') == 'true'

        show_extensions = request.form.get('showExtensions', 'false') == 'true'
        fib_high = request.form.get('fibHigh')
        show_fib = request.form.get('showFib', 'false') == 'true'
        include_financials = request.form.get('includeFinancials', 'true') == 'true'
        show_candlestick = request.form.get('showCandlestick', 'false') == 'true'

        # Handle moving averages with validation
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

        # Elliott Wave Support with validation
        elliott_points = None
        elliott_points_str = request.form.get('elliott_points', '')
        if elliott_points_str:
            try:
                elliott_points = json.loads(elliott_points_str)
            except json.JSONDecodeError as e:
                return jsonify(
                    error="Invalid Elliott wave points format",
                    validation_errors=[{"field": "elliott_points", "message": f"JSON decode error: {str(e)}"}]
                ), 400

        show_elliott_auto_waves = request.form.get('show_elliott_auto_waves', 'false') == 'true'

        # Elliott Wave enhancement settings
        elliott_fib_levels = None
        if chart_mode == 'elliott':
            show_elliott_fib = request.form.get('show_elliott_fib_levels', 'false') == 'true'
            extend_projections = request.form.get('extend_elliott_projections', 'true') == 'true'
            elliott_fib_levels = {
                'show_fib_levels': show_elliott_fib,
                'extend_projections': extend_projections
            }

        # Handle unified subplot configuration with comprehensive validation
        subplot_config = None
        subplot_config_str = request.form.get('subplotConfig', '')
        
        if subplot_config_str:
            # Parse and validate unified subplot configuration
            try:
                subplot_config = json.loads(subplot_config_str)
                print(f"DEBUG: Using unified subplot config: {subplot_config}")
                
                # Validate subplot configuration structure
                validation_errors = _validate_subplot_config_structure(subplot_config)
                if validation_errors:
                    return jsonify(
                        error="Invalid subplot configuration structure",
                        validation_errors=validation_errors
                    ), 400
                
            except json.JSONDecodeError as e:
                return jsonify(
                    error="Invalid subplot configuration JSON format",
                    validation_errors=[{"field": "subplotConfig", "message": f"JSON decode error: {str(e)}"}]
                ), 400
        else:
            # Fallback to individual flags for backward compatibility
            show_rsi = request.form.get('showRSI', 'false') == 'true'
            show_macd = request.form.get('showMACD', 'false') == 'true'
            show_volume = request.form.get('showVolume', 'false') == 'true'
            print(f"DEBUG: Using individual flags - RSI: {show_rsi}, MACD: {show_macd}, Volume: {show_volume}")

        # Validate subplot configuration if provided using SubplotManager
        if subplot_config:
            from sub_plots import SubplotManager
            subplot_manager = SubplotManager()
            
            requested_subplots = subplot_config.get('subplots', [])
            validation_result = subplot_manager.validate_subplot_combination(requested_subplots)
            
            if not validation_result.valid:
                # Return detailed conflict information to frontend
                return jsonify(
                    error="Subplot configuration conflicts detected",
                    conflicts=validation_result.conflicts,
                    suggestions=validation_result.suggestions,
                    alternatives=validation_result.alternative_configs,
                    max_subplots_exceeded=validation_result.max_subplots_exceeded,
                    available_subplots=subplot_manager.get_available_subplots()
                ), 400

        # Use StockPlotter to create the plot
        if subplot_config:
            # Use unified configuration
            result = stock_plotter.create_stock_plot(
                ticker=ticker,
                period=period,
                chart_mode=chart_mode,
                manual_fib=manual_fib,
                show_extensions=show_extensions,
                fib_high=fib_high,
                moving_averages=moving_averages,
                show_fib=show_fib,
                include_financials=include_financials,
                elliott_points=elliott_points,
                show_elliott_auto_waves=show_elliott_auto_waves,
                show_candlestick=show_candlestick,
                elliott_fib_levels=elliott_fib_levels,
                subplot_config=subplot_config  # Pass unified config
            )
        else:
            # Use individual flags (backward compatibility)
            result = stock_plotter.create_stock_plot(
                ticker=ticker,
                period=period,
                chart_mode=chart_mode,
                manual_fib=manual_fib,
                show_extensions=show_extensions,
                fib_high=fib_high,
                moving_averages=moving_averages,
                show_fib=show_fib,
                include_financials=include_financials,
                elliott_points=elliott_points,
                show_elliott_auto_waves=show_elliott_auto_waves,
                show_rsi=show_rsi,
                show_macd=show_macd,
                show_volume=show_volume,
                show_candlestick=show_candlestick,
                elliott_fib_levels=elliott_fib_levels
            )

        # Convert figure to JSON
        graph_json = json.dumps(result['figure'], cls=plotly.utils.PlotlyJSONEncoder)

        # Prepare enhanced response with layout metadata
        response_data = {
            'success': True,
            'graph': graph_json,
            'price': result['price_stats'],
            'financials': result['financial_metrics'],
            'priceTarget': result['price_target'],
            'ticker': ticker,
            'period': period
        }

        # Add layout metadata if available (from unified subplot configuration)
        if 'layout_info' in result:
            response_data['layoutInfo'] = {
                'subplotRows': result['layout_info']['subplot_rows'],
                'heightRatios': result['layout_info']['height_ratios'],
                'totalRows': result['layout_info']['total_rows'],
                'conflictsResolved': result['layout_info']['conflicts_resolved'],
                'warnings': result['layout_info']['warnings'],
                'priceChartDomain': result['layout_info'].get('price_chart_domain', [0.0, 1.0])
            }

        # Add validation result for successful requests with subplot config
        if subplot_config:
            response_data['validationResult'] = {
                'valid': True,
                'conflicts': [],
                'warnings': result.get('layout_info', {}).get('warnings', [])
            }

        return jsonify(response_data)

    except ValueError as e:
        return jsonify(
            error=f"Invalid parameter value: {str(e)}",
            validation_errors=[{"field": "general", "message": str(e)}]
        ), 400
    except Exception as e:
        print(f"Error in plot function: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify(
            error=f"An error occurred while generating the chart: {str(e)}",
            error_type="server_error"
        ), 500


def _validate_subplot_config_structure(subplot_config):
    """
    Validate the structure of the unified subplot configuration.
    
    Args:
        subplot_config: The parsed subplot configuration dictionary
        
    Returns:
        List of validation error dictionaries
    """
    validation_errors = []
    
    # Check if subplot_config is a dictionary
    if not isinstance(subplot_config, dict):
        validation_errors.append({
            "field": "subplotConfig",
            "message": "Subplot configuration must be a JSON object"
        })
        return validation_errors
    
    # Validate required fields
    if 'subplots' not in subplot_config:
        validation_errors.append({
            "field": "subplotConfig.subplots",
            "message": "Missing required field 'subplots'"
        })
    else:
        # Validate subplots field
        subplots = subplot_config['subplots']
        if not isinstance(subplots, list):
            validation_errors.append({
                "field": "subplotConfig.subplots",
                "message": "Field 'subplots' must be an array"
            })
        else:
            # Validate each subplot name
            for i, subplot in enumerate(subplots):
                if not isinstance(subplot, str):
                    validation_errors.append({
                        "field": f"subplotConfig.subplots[{i}]",
                        "message": f"Subplot name at index {i} must be a string"
                    })
                elif not subplot.strip():
                    validation_errors.append({
                        "field": f"subplotConfig.subplots[{i}]",
                        "message": f"Subplot name at index {i} cannot be empty"
                    })
    
    # Validate optional graph_settings field
    if 'graph_settings' in subplot_config:
        graph_settings = subplot_config['graph_settings']
        if not isinstance(graph_settings, dict):
            validation_errors.append({
                "field": "subplotConfig.graph_settings",
                "message": "Field 'graph_settings' must be an object"
            })
        else:
            # Validate known graph settings
            valid_settings = {'show_candlestick', 'show_graph_lines', 'show_time_selector'}
            for setting, value in graph_settings.items():
                if setting not in valid_settings:
                    validation_errors.append({
                        "field": f"subplotConfig.graph_settings.{setting}",
                        "message": f"Unknown graph setting '{setting}'. Valid settings: {', '.join(valid_settings)}"
                    })
                elif not isinstance(value, bool):
                    validation_errors.append({
                        "field": f"subplotConfig.graph_settings.{setting}",
                        "message": f"Graph setting '{setting}' must be a boolean value"
                    })
    
    # Validate optional layout_preferences field
    if 'layout_preferences' in subplot_config:
        layout_prefs = subplot_config['layout_preferences']
        if not isinstance(layout_prefs, dict):
            validation_errors.append({
                "field": "subplotConfig.layout_preferences",
                "message": "Field 'layout_preferences' must be an object"
            })
        else:
            # Validate known layout preferences
            if 'max_subplots' in layout_prefs:
                max_subplots = layout_prefs['max_subplots']
                if not isinstance(max_subplots, int) or max_subplots < 1 or max_subplots > 10:
                    validation_errors.append({
                        "field": "subplotConfig.layout_preferences.max_subplots",
                        "message": "Field 'max_subplots' must be an integer between 1 and 10"
                    })
            
            if 'min_price_height' in layout_prefs:
                min_price_height = layout_prefs['min_price_height']
                if not isinstance(min_price_height, (int, float)) or min_price_height < 0.1 or min_price_height > 0.9:
                    validation_errors.append({
                        "field": "subplotConfig.layout_preferences.min_price_height",
                        "message": "Field 'min_price_height' must be a number between 0.1 and 0.9"
                    })
    
    return validation_errors


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