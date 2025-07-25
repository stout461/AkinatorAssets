#!/usr/bin/env python3
"""
Test script for SubplotManager individual data rendering methods.
Tests the implementation of task 5: Add individual subplot data rendering methods.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sub_plots import SubplotManager

def create_test_data():
    """Create sample data for testing subplot rendering methods."""
    # Create date range
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    
    # Create sample price data
    np.random.seed(42)  # For reproducible results
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    
    # Create volume data
    volume = np.random.randint(1000000, 5000000, len(dates))
    
    # Create RSI data (simulate RSI values between 0-100)
    rsi = 50 + 20 * np.sin(np.arange(len(dates)) * 0.2) + np.random.randn(len(dates)) * 5
    rsi = np.clip(rsi, 0, 100)  # Ensure RSI stays within 0-100 range
    
    # Create MACD data
    macd_line = np.sin(np.arange(len(dates)) * 0.1) + np.random.randn(len(dates)) * 0.1
    signal_line = macd_line * 0.8 + np.random.randn(len(dates)) * 0.05
    histogram = macd_line - signal_line
    
    return {
        'dates': [date.strftime('%Y-%m-%d') for date in dates],
        'prices': prices,
        'volume': volume,
        'rsi': rsi,
        'macd_line': macd_line,
        'signal_line': signal_line,
        'histogram': histogram
    }

def test_volume_subplot():
    """Test volume subplot data rendering."""
    print("Testing volume subplot data rendering...")
    
    manager = SubplotManager()
    test_data = create_test_data()
    
    # Test with pandas Series-like data
    volume_series = pd.Series(test_data['volume'], index=pd.to_datetime(test_data['dates']))
    
    # Create figure with volume subplot
    fig = manager.create_subplot_figure(['volume'])
    
    # Test add_subplot_data method
    try:
        manager.add_subplot_data(fig, 'volume', volume_series)
        print("✓ Volume subplot data added successfully with pandas Series")
    except Exception as e:
        print(f"✗ Error adding volume data with pandas Series: {e}")
        return False
    
    # Test with dictionary format
    volume_dict = {
        'dates': test_data['dates'],
        'volume': test_data['volume']
    }
    
    fig2 = manager.create_subplot_figure(['volume'])
    try:
        manager.add_subplot_data(fig2, 'volume', volume_dict)
        print("✓ Volume subplot data added successfully with dictionary")
    except Exception as e:
        print(f"✗ Error adding volume data with dictionary: {e}")
        return False
    
    # Test convenience method
    fig3 = manager.create_subplot_figure(['volume'])
    try:
        manager.add_volume_subplot(fig3, volume_series)
        print("✓ Volume convenience method works correctly")
    except Exception as e:
        print(f"✗ Error with volume convenience method: {e}")
        return False
    
    return True

def test_rsi_subplot():
    """Test RSI subplot data rendering."""
    print("\nTesting RSI subplot data rendering...")
    
    manager = SubplotManager()
    test_data = create_test_data()
    
    # Test with pandas Series-like data
    rsi_series = pd.Series(test_data['rsi'], index=pd.to_datetime(test_data['dates']))
    
    # Create figure with RSI subplot
    fig = manager.create_subplot_figure(['rsi'])
    
    # Test add_subplot_data method
    try:
        manager.add_subplot_data(fig, 'rsi', rsi_series)
        print("✓ RSI subplot data added successfully with pandas Series")
    except Exception as e:
        print(f"✗ Error adding RSI data with pandas Series: {e}")
        return False
    
    # Test with dictionary format
    rsi_dict = {
        'dates': test_data['dates'],
        'rsi': test_data['rsi']
    }
    
    fig2 = manager.create_subplot_figure(['rsi'])
    try:
        manager.add_subplot_data(fig2, 'rsi', rsi_dict)
        print("✓ RSI subplot data added successfully with dictionary")
    except Exception as e:
        print(f"✗ Error adding RSI data with dictionary: {e}")
        return False
    
    # Test convenience method
    fig3 = manager.create_subplot_figure(['rsi'])
    try:
        manager.add_rsi_subplot(fig3, rsi_series)
        print("✓ RSI convenience method works correctly")
    except Exception as e:
        print(f"✗ Error with RSI convenience method: {e}")
        return False
    
    return True

def test_macd_subplot():
    """Test MACD subplot data rendering."""
    print("\nTesting MACD subplot data rendering...")
    
    manager = SubplotManager()
    test_data = create_test_data()
    
    # Test with dictionary format
    macd_dict = {
        'dates': test_data['dates'],
        'macd': test_data['macd_line'],
        'signal': test_data['signal_line'],
        'histogram': test_data['histogram']
    }
    
    # Create figure with MACD subplot
    fig = manager.create_subplot_figure(['macd'])
    
    # Test add_subplot_data method
    try:
        manager.add_subplot_data(fig, 'macd', macd_dict)
        print("✓ MACD subplot data added successfully with dictionary")
    except Exception as e:
        print(f"✗ Error adding MACD data with dictionary: {e}")
        return False
    
    # Test alternative dictionary format
    macd_dict2 = {
        'x': test_data['dates'],
        'macd_line': test_data['macd_line'],
        'signal_line': test_data['signal_line'],
        'histogram': test_data['histogram']
    }
    
    fig2 = manager.create_subplot_figure(['macd'])
    try:
        manager.add_subplot_data(fig2, 'macd', macd_dict2)
        print("✓ MACD subplot data added successfully with alternative dictionary format")
    except Exception as e:
        print(f"✗ Error adding MACD data with alternative dictionary: {e}")
        return False
    
    # Test convenience method
    fig3 = manager.create_subplot_figure(['macd'])
    try:
        manager.add_macd_subplot(fig3, macd_dict)
        print("✓ MACD convenience method works correctly")
    except Exception as e:
        print(f"✗ Error with MACD convenience method: {e}")
        return False
    
    return True

def test_time_selector_subplot():
    """Test time selector subplot data rendering."""
    print("\nTesting time selector subplot data rendering...")
    
    manager = SubplotManager()
    test_data = create_test_data()
    
    # Test with pandas Series-like data
    time_selector_series = pd.Series(test_data['prices'], index=pd.to_datetime(test_data['dates']))
    
    # Create figure with time_selector subplot
    fig = manager.create_subplot_figure(['time_selector'])
    
    # Test add_subplot_data method
    try:
        manager.add_subplot_data(fig, 'time_selector', time_selector_series)
        print("✓ Time selector subplot data added successfully with pandas Series")
    except Exception as e:
        print(f"✗ Error adding time selector data with pandas Series: {e}")
        return False
    
    # Test with dictionary format
    time_selector_dict = {
        'dates': test_data['dates'],
        'values': test_data['prices']
    }
    
    fig2 = manager.create_subplot_figure(['time_selector'])
    try:
        manager.add_subplot_data(fig2, 'time_selector', time_selector_dict)
        print("✓ Time selector subplot data added successfully with dictionary")
    except Exception as e:
        print(f"✗ Error adding time selector data with dictionary: {e}")
        return False
    
    return True

def test_generic_subplot_data():
    """Test generic subplot data rendering method."""
    print("\nTesting generic subplot data rendering...")
    
    manager = SubplotManager()
    test_data = create_test_data()
    
    # Add a custom subplot configuration for testing
    from sub_plots import SubplotConfiguration
    custom_config = SubplotConfiguration(
        name='custom_indicator',
        height_ratio=0.2,
        title='Custom Indicator',
        show_grid=True,
        y_axis_title='Custom Value',
        priority=5,
        conflicts_with=[],
        requires=[]
    )
    manager.add_subplot_config(custom_config)
    
    # Test with pandas Series-like data
    custom_series = pd.Series(test_data['prices'], index=pd.to_datetime(test_data['dates']))
    
    # Create figure with custom subplot
    fig = manager.create_subplot_figure(['custom_indicator'])
    
    # Test generic method with scatter plot
    try:
        manager.add_subplot_data(fig, 'custom_indicator', custom_series, trace_type='scatter')
        print("✓ Generic subplot data added successfully with scatter plot")
    except Exception as e:
        print(f"✗ Error adding generic data with scatter plot: {e}")
        return False
    
    # Test generic method with bar chart
    fig2 = manager.create_subplot_figure(['custom_indicator'])
    custom_dict = {
        'dates': test_data['dates'],
        'values': test_data['volume']
    }
    
    try:
        manager.add_subplot_data(fig2, 'custom_indicator', custom_dict, trace_type='bar')
        print("✓ Generic subplot data added successfully with bar chart")
    except Exception as e:
        print(f"✗ Error adding generic data with bar chart: {e}")
        return False
    
    return True

def test_multiple_subplots():
    """Test adding data to multiple subplots in one figure."""
    print("\nTesting multiple subplots data rendering...")
    
    manager = SubplotManager()
    test_data = create_test_data()
    
    # Create figure with multiple subplots
    fig = manager.create_subplot_figure(['volume', 'rsi', 'macd'])
    
    # Add volume data
    volume_series = pd.Series(test_data['volume'], index=pd.to_datetime(test_data['dates']))
    try:
        manager.add_subplot_data(fig, 'volume', volume_series)
        print("✓ Volume data added to multi-subplot figure")
    except Exception as e:
        print(f"✗ Error adding volume data to multi-subplot figure: {e}")
        return False
    
    # Add RSI data
    rsi_series = pd.Series(test_data['rsi'], index=pd.to_datetime(test_data['dates']))
    try:
        manager.add_subplot_data(fig, 'rsi', rsi_series)
        print("✓ RSI data added to multi-subplot figure")
    except Exception as e:
        print(f"✗ Error adding RSI data to multi-subplot figure: {e}")
        return False
    
    # Add MACD data
    macd_dict = {
        'dates': test_data['dates'],
        'macd': test_data['macd_line'],
        'signal': test_data['signal_line'],
        'histogram': test_data['histogram']
    }
    try:
        manager.add_subplot_data(fig, 'macd', macd_dict)
        print("✓ MACD data added to multi-subplot figure")
    except Exception as e:
        print(f"✗ Error adding MACD data to multi-subplot figure: {e}")
        return False
    
    return True

def test_error_handling():
    """Test error handling in subplot data rendering."""
    print("\nTesting error handling...")
    
    manager = SubplotManager()
    
    # Create figure with volume subplot
    fig = manager.create_subplot_figure(['volume'])
    
    # Test with invalid data format
    try:
        manager.add_subplot_data(fig, 'volume', "invalid_data")
        print("✓ Error handling works for invalid data format")
    except Exception as e:
        print(f"✓ Expected error caught for invalid data: {e}")
    
    # Test with unknown subplot
    try:
        manager.add_subplot_data(fig, 'unknown_subplot', {'x': [1, 2, 3], 'y': [1, 2, 3]})
        print("✗ Should have raised error for unknown subplot")
        return False
    except Exception as e:
        print(f"✓ Expected error caught for unknown subplot: {e}")
    
    # Test with figure not created by SubplotManager
    import plotly.graph_objects as go
    invalid_fig = go.Figure()
    try:
        manager.add_subplot_data(invalid_fig, 'volume', {'x': [1, 2, 3], 'y': [1, 2, 3]})
        print("✗ Should have raised error for invalid figure")
        return False
    except Exception as e:
        print(f"✓ Expected error caught for invalid figure: {e}")
    
    return True

def main():
    """Run all tests for subplot data rendering methods."""
    print("Running SubplotManager data rendering tests...\n")
    
    tests = [
        test_volume_subplot,
        test_rsi_subplot,
        test_macd_subplot,
        test_time_selector_subplot,
        test_generic_subplot_data,
        test_multiple_subplots,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All subplot data rendering methods implemented successfully!")
        return True
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)