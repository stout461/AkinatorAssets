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

    def get_stock_data(self, symbol, start_date, end_date):
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

    def detect_elliott_waves(self, prices, window=20):
        normalized_prices = (prices - prices.min()) / (prices.max() - prices.min())
        peaks, _ = find_peaks(normalized_prices, distance=window)
        troughs, _ = find_peaks(-normalized_prices, distance=window)
        return peaks, troughs

    def identify_wave_patterns(self, prices, peaks, troughs):
        patterns = []
        combined = sorted([(i, 'peak') for i in peaks] + [(i, 'trough') for i in troughs])

        for i in range(len(combined) - 4):
            pattern = combined[i:i+5]
            if all(p[1] != q[1] for p, q in zip(pattern, pattern[1:])):
                patterns.append({
                    'start': pattern[0][0],
                    'end': pattern[-1][0],
                    'points': pattern
                })

        return patterns

    def add_elliott_waves(self, fig, df, prices, x_dates, row=1, col=1):
        peaks, troughs = self.detect_elliott_waves(prices)
        patterns = self.identify_wave_patterns(prices, peaks, troughs)

        if patterns:
            # Take the most recent pattern
            recent_pattern = patterns[-1]
            pattern_points = recent_pattern['points']

            x_pattern = [df.index[p[0]].strftime('%Y-%m-%d') for p in pattern_points]
            y_pattern = [prices.iloc[p[0]] for p in pattern_points]
            labels = ['1', '2', '3', '4', '5']

            fig.add_trace(go.Scatter(
                x=x_pattern,
                y=y_pattern,
                mode='lines+markers+text',
                name='Elliott Wave',
                line=dict(color='purple', dash='dot', width=2),
                marker=dict(size=8),
                text=labels,
                textposition='top center',
                textfont=dict(size=12, color='purple')
            ), row=row, col=col)

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
                          show_fib=False, include_financials=True):
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

        Returns:
            dict: Contains figure, price stats, financial metrics, and price target
        """
        if not ticker:
            raise ValueError("Please enter a valid ticker symbol")

        # Get date range
        start_date, end_date = self.get_period_dates(period)

        # Fetch stock data
        df = self.get_stock_data(ticker, start_date, end_date)
        if df.empty:
            raise ValueError(f"No data found for ticker: {ticker}")

        # Create subplots
        fig = sp.make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=['Stock Price with Indicators', 'Relative Strength Index (RSI)', 'MACD']
        )

        # Convert index to datetime if needed
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        x_dates = df.index.strftime('%Y-%m-%d').tolist()
        y_values = df['Close'].tolist()

        # Add price trace
        fig.add_trace(go.Scatter(
            x=x_dates,
            y=y_values,
            mode='lines',
            name='Close Price',
            line=dict(color='#0ac775', width=2)
        ), row=1, col=1)

        # Add moving averages if specified
        if moving_averages and len(moving_averages) > 0:
            self.add_moving_averages(fig, df, x_dates, moving_averages, row=1, col=1)

        # Add Fibonacci lines if requested and toggled on
        if chart_mode == 'fib' and show_fib:
            fib_low_val = df['Close'].min()
            if manual_fib and fib_high:
                fib_high_val = float(fib_high)
            else:
                fib_high_val = df['Close'].max()
            self.add_fibonacci_lines(fig, x_dates, fib_high_val, fib_low_val, show_extensions, row=1, col=1)

        # Add Elliott Waves
        self.add_elliott_waves(fig, df, df['Close'], x_dates, row=1, col=1)

        # Add RSI subplot
        rsi = self.calculate_rsi(df['Close'])
        fig.add_trace(go.Scatter(
            x=x_dates,
            y=rsi.tolist(),
            mode='lines',
            name='RSI',
            line=dict(color='purple')
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        # Add MACD subplot
        macd_line, signal_line, histogram = self.calculate_macd(df['Close'])
        fig.add_trace(go.Scatter(
            x=x_dates,
            y=macd_line.tolist(),
            mode='lines',
            name='MACD',
            line=dict(color='blue')
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=x_dates,
            y=signal_line.tolist(),
            mode='lines',
            name='Signal Line',
            line=dict(color='red')
        ), row=3, col=1)
        colors = ['green' if val >= 0 else 'red' for val in histogram]
        fig.add_trace(go.Bar(
            x=x_dates,
            y=histogram.tolist(),
            name='Histogram',
            marker_color=colors
        ), row=3, col=1)

        # Update layout
        period_name = {
            "1M": "Past Month",
            "3M": "Past 3 Months",
            "6M": "Past 6 Months",
            "1Y": "Past Year",
            "5Y": "Past 5 Years"
        }.get(period, "Past Year")

        fig.update_layout(
            title=f"{ticker} Stock Price - {period_name}",
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis3_title="Date",
            yaxis_title="Price (USD)",
            yaxis2_title="RSI",
            yaxis3_title="MACD",
            template="plotly_white"
        )

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