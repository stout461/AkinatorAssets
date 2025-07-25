import pandas as pd
import plotly.graph_objs as go
import plotly.subplots as sp
import yfinance as yf
import time
import random
from datetime import datetime, timedelta
from scipy.signal import find_peaks


class StockPlotter:
    """
    A class to handle stock data fetching, processing, and plotting functionality.
    Separates plotting logic from the main Flask application.
    """

    def __init__(self):
        self.fib_levels_config = {
            'level0': {'ratio': 0.0, 'color': 'rgba(255, 0, 0, 0.7)', 'name': '0%'},
            'level236': {'ratio': 0.236, 'color': 'rgba(255, 165, 0, 0.7)', 'name': '23.6%'},
            'level382': {'ratio': 0.382, 'color': 'rgba(255, 255, 0, 0.7)', 'name': '38.2%'},
            'level50': {'ratio': 0.5, 'color': 'rgba(0, 128, 0, 0.7)', 'name': '50%'},
            'level618': {'ratio': 0.618, 'color': 'rgba(0, 0, 255, 0.7)', 'name': '61.8%'},
            'level786': {'ratio': 0.786, 'color': 'rgba(128, 0, 128, 0.7)', 'name': '78.6%'},
            'level100': {'ratio': 1.0, 'color': 'rgba(255, 0, 0, 0.7)', 'name': '100%'}
        }

        self.extension_config = {
            'ratios': [1.272, 1.382, 1.618, 2.618],
            'colors': ['#FF6666', '#FF8888', '#FFAAAA', '#FFC0CB']
        }

        # ADD: User-Defined Elliott Wave Projections - Define Fibonacci ratios for projections
        self.wave2_retracements = [0.5, 0.618, 0.764, 0.854]
        self.wave3_extensions = [1.0, 1.236, 1.382, 1.618, 2.0, 2.618]
        self.wave4_retracements = [0.146, 0.236, 0.382, .50, 0.618, 0.764]
        self.wave5_extensions = [1, 1.236, 1.618]  # For inverse of wave 4; additional handled in method

    @staticmethod
    def format_growth(value):
        """Convert value to percentage format"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value) * 100:.2f}%"
        except (ValueError, TypeError):
            return "N/A"

    @staticmethod
    def format_ratio(value):
        """Format ratio to 2 decimal places"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return "N/A"

    @staticmethod
    def format_revenue_billions(value):
        """Convert revenue to billions ($B)"""
        if value is None:
            return "N/A"
        try:
            return f"${float(value) / 1e9:.2f}B"
        except (ValueError, TypeError):
            return "N/A"

    def get_stock_data(self, symbol, start_date, end_date, period=None):
        """Fetch historical data from yfinance with appropriate interval based on period."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Determine the appropriate interval based on the period
            interval = self.get_optimal_interval(period)
            
            # For intervals other than daily, we need to use period instead of start/end dates
            if interval != '1d':
                # Map our period to yfinance period format
                yf_period = self.map_period_to_yfinance(period)
                df = ticker.history(period=yf_period, interval=interval)
            else:
                # Use start/end dates for daily data
                df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if not df.empty and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df = df.dropna()
            return df
        except Exception as e:
            print(f"Error getting data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_optimal_interval(self, period):
        """Determine the optimal candlestick interval based on the time period."""
        if period == '1M':
            return '1h'    # 1-hour candlesticks for 1 month
        elif period == '3M':
            return '4h'    # 4-hour candlesticks for 3 months
        elif period == '6M':
            return '1d'    # Daily candlesticks for 6 months
        elif period == '1Y':
            return '1d'    # Daily candlesticks for 1 year
        elif period == '5Y':
            return '1wk'   # Weekly candlesticks for 5 years
        else:
            return '1d'    # Default to daily
    
    def map_period_to_yfinance(self, period):
        """Map our period format to yfinance period format."""
        period_map = {
            '1M': '1mo',
            '3M': '3mo',
            '6M': '6mo',
            '1Y': '1y',
            '5Y': '5y'
        }
        return period_map.get(period, '1y')

    def get_yfinance_data(self, symbol):
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

    def calculate_future_value(self, revenue, revenue_growth, market_cap, trailing_pe, profit_margin):
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

    def get_period_dates(self, period):
        """Convert period string to start and end dates."""
        end_date = datetime.now()
        period_mapping = {
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
            '5Y': 365 * 5
        }

        days = period_mapping.get(period, 365)
        start_date = end_date - timedelta(days=days)
        return start_date, end_date

    def calculate_price_stats(self, df):
        """Calculate price statistics from stock data."""
        current_price = df['Close'].iloc[-1]
        first_price = df['Close'].iloc[0]
        period_change = ((current_price / first_price) - 1) * 100
        high_price = df['High'].max()
        low_price = df['Low'].min()

        return {
            "current": f"${current_price:.2f}",
            "change": f"{period_change:.2f}%",
            "high": f"${high_price:.2f}",
            "low": f"${low_price:.2f}"
        }

    def format_financial_metrics(self, financial_data):
        """Format financial metrics for display."""
        return {
            "revenueGrowth": self.format_growth(financial_data.get('revenueGrowth')),
            "forwardPE": self.format_ratio(financial_data.get('forwardPE')),
            "trailingPE": self.format_ratio(financial_data.get('trailingPE')),
            "profitMargin": self.format_growth(financial_data.get('profitMargins')),
            "priceToSales": self.format_ratio(financial_data.get('priceToSalesTrailing12Months')),
            "totalRevenue": self.format_revenue_billions(financial_data.get('totalRevenue')),
            "marketCap": self.format_revenue_billions(financial_data.get('marketCap'))
        }

    def calculate_price_target(self, financial_data):
        """Calculate price target based on financial data."""
        revenue = financial_data.get('totalRevenue')
        revenue_growth = financial_data.get('revenueGrowth')
        market_cap = financial_data.get('marketCap')
        trailing_pe = financial_data.get('trailingPE')
        profit_margin = financial_data.get('profitMargins')

        if profit_margin is not None:
            profit_margin *= 100

        future_value, rate_increase, adjustments = self.calculate_future_value(
            revenue, revenue_growth, market_cap, trailing_pe, profit_margin
        )

        return {
            "futureValue": None if future_value is None else f"${future_value}B",
            "rateIncrease": None if rate_increase is None else f"{rate_increase}x",
            "adjustments": adjustments
        }

    def calculate_moving_average(self, df, period=20, column='Close'):
        """
        Calculate moving average for a given period.

        Args:
            df: DataFrame with stock data
            period: Number of periods for moving average (default: 20)
            column: Column to calculate moving average on (default: 'Close')

        Returns:
            pandas.Series: Moving average values
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        return df[column].rolling(window=period, min_periods=1).mean()

    def calculate_rsi(self, prices, window=14):
        """
        Calculate Relative Strength Index (RSI).
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, prices, slow=26, fast=12, signal=9):
        """
        Calculate Moving Average Convergence Divergence (MACD).
        """
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    # TODO Improve the Elliott Wave detection logic
    def detect_elliott_waves(self, prices, min_distance=None, prominence=0.02):
        if min_distance is None:
            min_distance = max(5, len(prices) // 40)  # Adaptive
        smoothed = prices.ewm(span=3).mean()  # Light smoothing
        normalized_prices = (smoothed - smoothed.min()) / (smoothed.max() - smoothed.min() + 1e-8)
        peaks, _ = find_peaks(normalized_prices, distance=min_distance, prominence=prominence)
        troughs, _ = find_peaks(-normalized_prices, distance=min_distance, prominence=prominence)
        return peaks, troughs

    def validate_impulse(self, prices, points):
        if len(points) != 6:
            return False
        p = [prices.iloc[pt[0]] for pt in points]
        is_up = p[5] > p[0]

        w = [p[j+1] - p[j] for j in range(5)]

        if is_up:
            # Main waves >0, corrective <0
            if w[0] <=0 or w[2] <=0 or w[4] <=0 or w[1] >=0 or w[3] >=0:
                return False
            w_len = [abs(w[i]) for i in range(5)]
            overlap = p[4] < p[1]
        else:
            # Main <0, corrective >0
            if w[0] >=0 or w[2] >=0 or w[4] >=0 or w[1] <=0 or w[3] <=0:
                return False
            w_len = [abs(w[i]) for i in range(5)]
            overlap = p[4] > p[1]

        w1_len, w2_len, w3_len, w4_len, w5_len = w_len

        # Wave 3 not shortest (relaxed to >80%)
        if w3_len < 0.8 * max(w1_len, w5_len):
            return False

        # Wave 2 retrace <100%, >30%
        retr2 = w2_len / w1_len
        if retr2 >= 1 or retr2 < 0.3:
            return False

        # Wave 4 retrace <50%, >20%
        retr4 = w4_len / w3_len
        if retr4 >= 0.5 or retr4 < 0.2:
            return False

        # No overlap
        if overlap:
            return False

        return True

    def validate_correction(self, prices, points):
        if len(points) != 4:
            return False
        p = [prices.iloc[pt[0]] for pt in points]
        is_down = p[3] < p[0]

        w = [p[j+1] - p[j] for j in range(3)]

        if is_down:
            # A <0, C <0, B >0
            if w[0] >=0 or w[2] >=0 or w[1] <=0:
                return False
            w_len = [abs(w[i]) for i in range(3)]
        else:
            # A >0, C >0, B <0
            if w[0] <=0 or w[2] <=0 or w[1] >=0:
                return False
            w_len = [abs(w[i]) for i in range(3)]

        wa_len, wb_len, wc_len = w_len

        # Wave C ~ A (0.618-1.618)
        ratio_c = wc_len / wa_len
        if ratio_c < 0.618 or ratio_c > 1.618:
            return False

        # Wave B retrace 38-78%
        retr_b = wb_len / wa_len
        if retr_b < 0.38 or retr_b > 0.78:
            return False

        return True

    def identify_wave_patterns(self, prices, peaks, troughs):
        patterns = {'impulse': [], 'correction': []}
        combined = sorted([(i, 'peak') for i in peaks] + [(i, 'trough') for i in troughs])

        i = 0
        while i < len(combined) - 3:
            # Look for 6-point impulse
            if len(combined) - i >= 6:
                impulse = combined[i:i+6]
                if all(p[1] != q[1] for p, q in zip(impulse, impulse[1:])):
                    if self.validate_impulse(prices, impulse):
                        patterns['impulse'].append({
                            'start': impulse[0][0],
                            'end': impulse[5][0],
                            'points': impulse
                        })
                        i += 5
                        # Look for 4-point correction
                        if len(combined) - i >= 4:
                            correction = combined[i:i+4]
                            if all(p[1] != q[1] for p, q in zip(correction, correction[1:])):
                                if self.validate_correction(prices, correction):
                                    patterns['correction'].append({
                                        'start': correction[0][0],
                                        'end': correction[3][0],
                                        'points': correction
                                    })
                                    i += 4
                                    continue
            # Look for standalone 4-point correction
            if len(combined) - i >= 4:
                correction = combined[i:i+4]
                if all(p[1] != q[1] for p, q in zip(correction, correction[1:])):
                    if self.validate_correction(prices, correction):
                        patterns['correction'].append({
                            'start': correction[0][0],
                            'end': correction[3][0],
                            'points': correction
                        })
                        i += 4
                        continue
            i += 1

        return patterns

    # Renamed from add_elliott_waves (original auto-detection)
    def add_auto_elliott_waves(self, fig, df, prices, x_dates, row=1, col=1):
        peaks, troughs = self.detect_elliott_waves(prices)
        patterns = self.identify_wave_patterns(prices, peaks, troughs)

        # Plot only the last impulse if any
        if patterns['impulse']:
            pattern = patterns['impulse'][-1]
            points = pattern['points']
            x_pattern = [df.index[p[0]].strftime('%Y-%m-%d') for p in points]
            y_pattern = [prices.iloc[p[0]] for p in points]
            labels = ['0', '1', '2', '3', '4', '5'] if len(points) == 6 else []

            fig.add_trace(go.Scatter(
                x=x_pattern,
                y=y_pattern,
                mode='lines',
                name='Impulse',
                line=dict(color='blue', width=1.5),
                hovertemplate='Price: %{y:.2f}<extra></extra>'
            ), row=row, col=1)

            # Add boxed labels
            for j, label in enumerate(labels):
                fig.add_annotation(
                    x=x_pattern[j],
                    y=y_pattern[j],
                    text=label,
                    showarrow=False,
                    font=dict(color='blue', size=10),
                    bgcolor='white',
                    bordercolor='blue',
                    borderwidth=1,
                    borderpad=2,
                    opacity=0.8
                )

        # Plot only the last correction if any
        if patterns['correction']:
            pattern = patterns['correction'][-1]
            points = pattern['points']
            x_pattern = [df.index[p[0]].strftime('%Y-%m-%d') for p in points]
            y_pattern = [prices.iloc[p[0]] for p in points]
            labels = ['0', 'A', 'B', 'C'] if len(points) == 4 else []

            fig.add_trace(go.Scatter(
                x=x_pattern,
                y=y_pattern,
                mode='lines',
                name='Correction',
                line=dict(color='red', dash='dash', width=1.5),
                hovertemplate='Price: %{y:.2f}<extra></extra>'
            ), row=row, col=1)

            # Add boxed labels
            for j, label in enumerate(labels):
                fig.add_annotation(
                    x=x_pattern[j],
                    y=y_pattern[j],
                    text=label,
                    showarrow=False,
                    font=dict(color='red', size=10),
                    bgcolor='white',
                    bordercolor='red',
                    borderwidth=1,
                    borderpad=2,
                    opacity=0.8
                )

    # ADD: User-Defined Elliott Wave Projections with Enhanced Features
    def add_user_elliott_waves(self, fig, x_dates, elliott_points, row=1, col=1,
                               show_fib_levels=False, extend_projections=True):
        if not elliott_points or len(elliott_points) < 2:
            return

        num_points = len(elliott_points)
        x_wave = [p['x'] for p in elliott_points]
        y_wave = [float(p['y']) for p in elliott_points]

        # Draw user-defined wave lines and markers
        fig.add_trace(go.Scatter(
            x=x_wave,
            y=y_wave,
            mode='lines+markers',
            name='User Elliott Waves',
            line=dict(color='purple', width=2),
            marker=dict(size=8),
            hovertemplate='Price: %{y:.2f}<extra></extra>'
        ), row=row, col=1)

        # Add labels (0,1,2,3,4,5)
        labels = ['0', '1', '2', '3', '4', '5'][:num_points]
        for i, label in enumerate(labels):
            fig.add_annotation(
                x=x_wave[i],
                y=y_wave[i],
                text=label,
                showarrow=False,
                font=dict(color='purple', size=12),
                bgcolor='white',
                bordercolor='purple',
                borderwidth=1,
                borderpad=2,
                opacity=0.8
            )

        # No projections if 6+ points (full impulse or more)
        if num_points >= 6:
            return

        # Determine direction from Wave 1 (points 0 to 1)
        wave1_delta = y_wave[1] - y_wave[0]
        is_up = wave1_delta > 0

        # Extend projections well into the future to handle chart panning
        from datetime import datetime, timedelta
        last_date_obj = datetime.strptime(x_dates[-1], '%Y-%m-%d')
        extended_date = last_date_obj + timedelta(days=365)  # Extend 1 year into future
        extended_date_str = extended_date.strftime('%Y-%m-%d')

        if num_points == 2:
            # Project Wave 2 retracements of Wave 1 (corrective)
            proj_color = 'red' if is_up else 'green'
            wave1_len = abs(y_wave[1] - y_wave[0])
            for retr in self.wave2_retracements:
                if is_up:
                    target = y_wave[1] - retr * wave1_len
                else:
                    target = y_wave[1] + retr * wave1_len
                fig.add_trace(go.Scatter(
                    x=[x_wave[-1], extended_date_str],
                    y=[target, target],
                    mode='lines',
                    line=dict(dash='dash', color=proj_color, width=1),
                    name=f'W2 {retr*100:.1f}% Retr.',
                    hoverinfo='name+y'
                ), row=row, col=1)
                fig.add_annotation(
                    x=extended_date_str,
                    y=target,
                    text=f'W2 {retr*100:.1f}%',
                    showarrow=False,
                    xanchor='left',
                    font=dict(color='purple', size=10)
                )

        elif num_points == 3:
            # Project Wave 3 extensions of Wave 1 from end of Wave 2 (impulsive)
            proj_color = 'green' if is_up else 'red'
            wave1_len = abs(y_wave[1] - y_wave[0])
            wave2_end = y_wave[2]
            for ext in self.wave3_extensions:
                if is_up:
                    target = wave2_end + ext * wave1_len
                else:
                    target = wave2_end - ext * wave1_len
                fig.add_trace(go.Scatter(
                    x=[x_wave[-1], extended_date_str],
                    y=[target, target],
                    mode='lines',
                    line=dict(dash='dash', color=proj_color, width=1),
                    name=f'W3 {ext*100:.1f}% Ext.',
                    hoverinfo='name+y'
                ), row=row, col=1)
                fig.add_annotation(
                    x=extended_date_str,
                    y=target,
                    text=f'W3 {ext*100:.1f}%',
                    showarrow=False,
                    xanchor='left',
                    font=dict(color='purple', size=10)
                )

        elif num_points == 4:
            # Project Wave 4 retracements of Wave 3 (corrective)
            proj_color = 'red' if is_up else 'green'
            wave3_start = y_wave[2]
            wave3_end = y_wave[3]
            wave3_len = abs(wave3_end - wave3_start)

            for retr in self.wave4_retracements:
                if is_up:
                    target = wave3_end - retr * wave3_len
                else:
                    target = wave3_end + retr * wave3_len
                fig.add_trace(go.Scatter(
                    x=[x_wave[-1], extended_date_str],
                    y=[target, target],
                    mode='lines',
                    line=dict(dash='dash', color=proj_color, width=1),
                    name=f'W4 {retr*100:.1f}% Retr.',
                    hoverinfo='name+y'
                ), row=row, col=1)
                fig.add_annotation(
                    x=extended_date_str,
                    y=target,
                    text=f'W4 {retr*100:.1f}%',
                    showarrow=False,
                    xanchor='left',
                    font=dict(color='purple', size=10)
                )

        elif num_points == 5:
            # Project Wave 5 using multiple Fibonacci methods (impulsive)
            proj_color = 'green' if is_up else 'red'
            wave4_end = y_wave[4]
            wave1_len = abs(y_wave[1] - y_wave[0])
            wave13_len = abs(y_wave[3] - y_wave[0])
            wave4_len = abs(y_wave[4] - y_wave[3])

            # Method 1: Equal to Wave 1
            target_eq = wave4_end + wave1_len if is_up else wave4_end - wave1_len
            fig.add_trace(go.Scatter(
                x=[x_wave[-1], extended_date_str],
                y=[target_eq, target_eq],
                mode='lines',
                line=dict(dash='dash', color=proj_color, width=1),
                name='W5 = W1',
                hoverinfo='name+y'
            ), row=row, col=1)
            fig.add_annotation(
                x=extended_date_str,
                y=target_eq,
                text='W5 = W1',
                showarrow=False,
                xanchor='left',
                font=dict(color='purple', size=10)
            )

            # Method 2: 61.8% of Waves 1+3 (from 0 to 3)
            target_618 = wave4_end + 0.618 * wave13_len if is_up else wave4_end - 0.618 * wave13_len
            fig.add_trace(go.Scatter(
                x=[x_wave[-1], extended_date_str],
                y=[target_618, target_618],
                mode='lines',
                line=dict(dash='dash', color=proj_color, width=1),
                name='W5 61.8% W1+3',
                hoverinfo='name+y'
            ), row=row, col=1)
            fig.add_annotation(
                x=extended_date_str,
                y=target_618,
                text='W5 61.8% W1+3',
                showarrow=False,
                xanchor='left',
                font=dict(color='purple', size=10)
            )

            # Method 3: Inverse 1.236-1.618% extension of Wave 4
            for ext in self.wave5_extensions:
                target = wave4_end + ext * wave4_len if is_up else wave4_end - ext * wave4_len
                fig.add_trace(go.Scatter(
                    x=[x_wave[-1], extended_date_str],
                    y=[target, target],
                    mode='lines',
                    line=dict(dash='dash', color=proj_color, width=1),
                    name=f'W5 {ext*100:.1f}% W4',
                    hoverinfo='name+y'
                ), row=row, col=1)
                fig.add_annotation(
                    x=extended_date_str,
                    y=target,
                    text=f'W5 {ext*100:.1f}% W4',
                    showarrow=False,
                    xanchor='left',
                    font=dict(color='purple', size=10)
                )

    def add_moving_averages(self, fig, df, x_dates, ma_periods=None, row=1, col=1):
        """
        Add moving average lines to the plot.

        Args:
            fig: Plotly figure object
            df: DataFrame with stock data
            x_dates: List of x-axis dates
            ma_periods: List of periods for moving averages (e.g., [20, 50, 200])
        """
        if ma_periods is None:
            ma_periods = [20, 50]

        # Color scheme for different moving averages
        ma_colors = {
            5: '#FF6B6B',    # Light red
            10: '#4ECDC4',   # Teal
            20: '#45B7D1',   # Blue
            50: '#96CEB4',   # Light green
            100: '#FFEAA7',  # Light yellow
            200: '#DDA0DD'   # Plum
        }

        # Default colors for other periods
        default_colors = ['#FF8C42', '#6A4C93', '#C44569', '#F8B500', '#38A3A5']

        for i, period in enumerate(ma_periods):
            try:
                ma_values = self.calculate_moving_average(df, period)

                # Get color for this moving average
                if period in ma_colors:
                    color = ma_colors[period]
                else:
                    color = default_colors[i % len(default_colors)]

                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=ma_values.tolist(),
                    mode='lines',
                    name=f'MA{period}',
                    line=dict(
                        color=color,
                        width=2,
                        dash='dot' if period > 50 else 'solid'
                    ),
                    hovertemplate=f'<b>MA{period}</b><br>' +
                                  'Date: %{x}<br>' +
                                  'Price: $%{y:.2f}<extra></extra>'
                ), row=row, col=col)

            except Exception as e:
                print(f"Error calculating MA{period}: {str(e)}")
                continue

    def add_fibonacci_lines(self, fig, x_dates, fib_high_val, fib_low_val, show_extensions=False, row=1, col=1):
        """Add Fibonacci retracement and extension lines to the plot."""
        price_range = fib_high_val - fib_low_val

        # Standard retracement levels
        for level_key, config in self.fib_levels_config.items():
            value = fib_high_val - config['ratio'] * price_range
            fig.add_trace(go.Scatter(
                x=x_dates,
                y=[value] * len(x_dates),
                mode='lines',
                line=dict(
                    color=config['color'],
                    width=1,
                    dash='dash'
                ),
                name=f"{config['name']} - ${value:.2f}",
                hoverinfo='name+y'
            ), row=row, col=col)

        # Optional extension lines
        if show_extensions:
            for i, ratio in enumerate(self.extension_config['ratios']):
                extension_value = fib_high_val + (ratio - 1) * price_range
                ratio_percent = ratio * 100

                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=[extension_value] * len(x_dates),
                    mode='lines',
                    line=dict(
                        color=self.extension_config['colors'][i],
                        width=1,
                        dash='dash'
                    ),
                    name=f"{ratio_percent:.1f}% - ${extension_value:.2f}",
                    hoverinfo='name+y'
                ), row=row, col=col)

    def create_stock_plot(self, ticker, period, chart_mode='fib', manual_fib=False,
                          show_extensions=False, fib_high=None, moving_averages=None,
                          show_fib=False, include_financials=True, elliott_points=None,
                          show_elliott_auto_waves=False, show_rsi=False, show_macd=False,
                          show_volume=False, show_candlestick=False, elliott_fib_levels=None):

        """
        Create a complete stock plot with price data and optional indicators.

        Args:
            ticker: Stock symbol
            period: Time period ('1M', '3M', '6M', '1Y', '5Y')
            chart_mode: 'fib' or 'trendlines'
            manual_fib: Whether to show manual Fibonacci lines
            show_extensions: Whether to show extension lines
            fib_high: High value for Fibonacci calculations
            moving_averages: List of moving average periods (e.g., [20, 50, 200])
            show_fib: Whether to show Fibonacci lines (default: False)
            include_financials: Whether to include financial metrics (default: True)
            elliott_points: List of user-defined points for Elliott waves (default: None)
            show_elliott_auto_waves: Whether to show auto-generated Elliott waves (default: False)
            show_rsi: Whether to show RSI subplot (default: False)
            show_macd: Whether to show MACD subplot (default: False)
            show_volume: Whether to show volume subplot (default: False)
            show_candlestick: Whether to use candlestick or line for price (default: True)
            elliott_fib_levels: Elliott wave enhancement settings (default: None)

        Returns:
            dict: Contains figure, price stats, financial metrics, and price target
        """
        if not ticker:
            raise ValueError("Please enter a valid ticker symbol")

        # Get date range
        start_date, end_date = self.get_period_dates(period)

        # Fetch stock data
        df = self.get_stock_data(ticker, start_date, end_date, period)
        if df.empty:
            raise ValueError(f"No data found for ticker: {ticker}")

        # Create dynamic subplots based on indicators
        subplot_count = 1  # Always price
        row_heights = [1.0]  # Initial price height
        volume_row = None
        rsi_row = None
        macd_row = None
        current_row = 2  # Start after price row (1)

        if show_volume:
            volume_row = current_row
            subplot_count += 1
            row_heights.append(0.2)
            current_row += 1

        if show_rsi:
            rsi_row = current_row
            subplot_count += 1
            row_heights.append(0.2)
            current_row += 1

        if show_macd:
            macd_row = current_row
            subplot_count += 1
            row_heights.append(0.2)

        # Normalize heights to sum to 1.0
        total_height_sum = sum(row_heights)
        row_heights = [h / total_height_sum for h in row_heights]

        fig = sp.make_subplots(
            rows=subplot_count, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
            subplot_titles=[''] * subplot_count
        )

        # Convert index to datetime if needed
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        x_dates = df.index.strftime('%Y-%m-%d').tolist()
        y_values = df['Close'].tolist()

        # Add price trace (candlestick or line)
        if show_candlestick:
            # Check if OHLC columns exist
            required_cols = ['Open', 'High', 'Low', 'Close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Warning: Missing OHLC columns for candlestick: {missing_cols}")
                print(f"Available columns: {df.columns.tolist()}")
                # Fallback to line chart if OHLC data is missing
                price_trace = go.Scatter(
                    x=x_dates,
                    y=y_values,
                    mode='lines',
                    name='Close Price (Fallback)',
                    line=dict(color='#0ac775', width=2)
                )
            else:
                price_trace = go.Candlestick(
                    x=x_dates,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='Price',
                    increasing_line_color='#22c55e',
                    decreasing_line_color='#ef4444',
                    increasing_fillcolor='#22c55e',
                    decreasing_fillcolor='#ef4444'
                )
        else:
            price_trace = go.Scatter(
                x=x_dates,
                y=y_values,
                mode='lines',
                name='Close Price',
                line=dict(color='#0ac775', width=2)
            )
        
        fig.add_trace(price_trace, row=1, col=1)

        # Add Fibonacci lines if requested and toggled on
        if chart_mode == 'fib' and show_fib:
            fib_low_val = df['Close'].min()
            if manual_fib and fib_high:
                fib_high_val = float(fib_high)
            else:
                fib_high_val = df['Close'].max()
            self.add_fibonacci_lines(fig, x_dates, fib_high_val, fib_low_val, show_extensions, row=1, col=1)

        # ADD: User-Defined Elliott Wave Projections - Add auto waves only if enabled, user projections if provided
        if elliott_points:
            # Get Elliott Wave enhancement settings from frontend
            show_fib_levels = elliott_fib_levels is not None and elliott_fib_levels.get('show_fib_levels', False)
            extend_projections = elliott_fib_levels is None or elliott_fib_levels.get('extend_projections', True)

            self.add_user_elliott_waves(fig, x_dates, elliott_points, row=1, col=1,
                                        show_fib_levels=show_fib_levels,
                                        extend_projections=extend_projections)
        elif show_elliott_auto_waves:
            # Only show auto-generated Elliott waves if the user has enabled the toggle
            self.add_auto_elliott_waves(fig, df, df['Close'], x_dates, row=1, col=1)

        # Add volume if toggled
        if show_volume:
            colors = ['#22c55e' if row['Close'] > row['Open'] else '#ef4444' for _, row in df.iterrows()]
            volume_bar = go.Bar(
                x=x_dates,
                y=df['Volume'].tolist(),
                name='Volume',
                marker_color=colors,
                opacity=0.8  # Increased opacity for better visibility
            )
            fig.add_trace(volume_bar, row=volume_row, col=1)

        # Add RSI subplot if requested
        if show_rsi:
            rsi = self.calculate_rsi(df['Close'])
            fig.add_trace(go.Scatter(
                x=x_dates,
                y=rsi.tolist(),
                mode='lines',
                name='RSI',
                line=dict(color='#9C27B0', width=2)
            ), row=rsi_row, col=1)

            # Add RSI overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red",
                          row=rsi_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green",
                          row=rsi_row, col=1)
            fig.update_yaxes(range=[0,100], row=rsi_row, col=1)

        # Add MACD subplot if requested
        if show_macd:
            macd_line, signal_line, histogram = self.calculate_macd(df['Close'])

            # MACD Line
            fig.add_trace(go.Scatter(
                x=x_dates,
                y=macd_line.tolist(),
                mode='lines',
                name='MACD',
                line=dict(color='#2196F3', width=2)
            ), row=macd_row, col=1)

            # Signal Line
            fig.add_trace(go.Scatter(
                x=x_dates,
                y=signal_line.tolist(),
                mode='lines',
                name='Signal Line',
                line=dict(color='#FF5722', width=2)
            ), row=macd_row, col=1)

            # Histogram
            colors = ['#4CAF50' if val >= 0 else '#F44336' for val in histogram]
            fig.add_trace(go.Bar(
                x=x_dates,
                y=histogram.tolist(),
                name='Histogram',
                marker_color=colors,
                opacity=0.7
            ), row=macd_row, col=1)

            # Add zero line
            fig.add_hline(y=0, line_dash="solid", line_color="gray",
                          line_width=1, row=macd_row, col=1)

        # Add moving averages if specified
        if moving_averages and len(moving_averages) > 0:
            self.add_moving_averages(fig, df, x_dates, moving_averages, row=1, col=1)

        # Update layout with modern styling
        period_name = {
            "1M": "Past Month",
            "3M": "Past 3 Months",
            "6M": "Past 6 Months",
            "1Y": "Past Year",
            "5Y": "Past 5 Years"
        }.get(period, "Past Year")

        # Calculate dynamic height based on subplots
        base_height = 600
        subplot_height = 200
        total_height = base_height + (subplot_count - 1) * subplot_height

        fig.update_layout(
            title=dict(
                text=f"{ticker} Stock Price - {period_name}",
                font=dict(size=20, color='#000000'),
                x=0.5,
                xanchor='center'
            ),
            height=total_height,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5,
                bgcolor="white",
                bordercolor="rgba(0,0,0,0.1)",
                borderwidth=1
            ),
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(l=60, r=60, t=80, b=60),
            hovermode='x unified',
            # Disable the automatic range slider that appears with candlestick charts
            xaxis=dict(
                rangeslider=dict(visible=False),
                type='date'
            )
        )

        # Update axis titles dynamically and disable range slider for all x-axes
        fig.update_xaxes(title_text="Date", row=subplot_count, col=1, rangeslider=dict(visible=False))
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=volume_row, col=1)
        
        # Ensure range slider is disabled for all x-axes
        for i in range(1, subplot_count + 1):
            fig.update_xaxes(rangeslider=dict(visible=False), row=i, col=1)
        if show_rsi:
            fig.update_yaxes(title_text="RSI", row=rsi_row, col=1)
        if show_macd:
            fig.update_yaxes(title_text="MACD", row=macd_row, col=1)

        # Cleaner grid: faint for price, none for others
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', gridwidth=1, row=1, col=1)
        if show_volume:
            fig.update_yaxes(showgrid=False, row=volume_row, col=1)
        if show_rsi:
            fig.update_yaxes(showgrid=False, row=rsi_row, col=1)
        if show_macd:
            fig.update_yaxes(showgrid=False, row=macd_row, col=1)

        # Get financial data
        if include_financials:
            financial_data = self.get_yfinance_data(ticker)
        else:
            financial_data = {}

        # Calculate statistics
        price_stats = self.calculate_price_stats(df)
        financial_metrics = self.format_financial_metrics(financial_data)
        price_target = self.calculate_price_target(financial_data)

        return {
            'figure': fig,
            'price_stats': price_stats,
            'financial_metrics': financial_metrics,
            'price_target': price_target
        }