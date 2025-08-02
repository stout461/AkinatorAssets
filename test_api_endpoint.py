#!/usr/bin/env python3
"""
Test script to simulate the API endpoint and see what error occurs.
"""

import sys
import os
sys.path.append('src')

def test_stock_plot_creation():
    """Test creating a stock plot like the API endpoint does."""
    
    try:
        from stock_plotter import StockPlotter
        print("✓ StockPlotter import successful")
        
        # Initialize stock plotter
        stock_plotter = StockPlotter()
        print("✓ StockPlotter initialization successful")
        
        # Test parameters similar to what the API would receive
        ticker = 'AAPL'
        period = '1M'
        chart_mode = 'fib'
        show_volume = True
        show_candlestick = True
        
        print(f"Testing stock plot creation for {ticker}...")
        
        # Try to create the plot
        result = stock_plotter.create_stock_plot(
            ticker=ticker,
            period=period,
            chart_mode=chart_mode,
            manual_fib=False,
            show_extensions=False,
            fib_high=None,
            moving_averages=None,
            show_fib=False,
            include_financials=True,
            elliott_points=None,
            show_elliott_auto_waves=False,
            show_rsi=False,
            show_macd=False,
            show_volume=show_volume,
            show_candlestick=show_candlestick,
            elliott_fib_levels=None,
            subplot_config=None
        )
        
        print("✓ Stock plot creation successful")
        print(f"  - Figure type: {type(result['figure'])}")
        print(f"  - Price stats: {result['price_stats']}")
        print(f"  - Has financial metrics: {'financial_metrics' in result}")
        
        # Test with subplot config
        print("\nTesting with subplot configuration...")
        subplot_config = {'subplots': ['volume']}
        
        result2 = stock_plotter.create_stock_plot(
            ticker=ticker,
            period=period,
            chart_mode=chart_mode,
            subplot_config=subplot_config,
            show_candlestick=True
        )
        
        print("✓ Stock plot with subplot config successful")
        print(f"  - Has layout info: {'layout_info' in result2}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stock_plot_creation()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")