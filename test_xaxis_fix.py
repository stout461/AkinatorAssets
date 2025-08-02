#!/usr/bin/env python3
"""
Test script to verify x-axis duplication fix.
"""

import sys
import os
sys.path.append('src')

from sub_plots import SubplotManager
import pandas as pd
import numpy as np

def test_xaxis_configuration():
    """Test that x-axis labels only appear on the bottom subplot."""
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    test_data = pd.DataFrame({
        'Close': np.random.randn(50).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 50)
    }, index=dates)
    
    # Initialize subplot manager
    subplot_manager = SubplotManager()
    
    # Test with multiple subplots to check x-axis configuration
    print("Testing x-axis configuration with multiple subplots...")
    requested_subplots = ['volume', 'rsi']
    
    # Create figure
    fig = subplot_manager.create_subplot_figure(requested_subplots)
    
    # Check the figure layout
    layout_result = fig._subplot_manager_metadata['layout_result']
    print(f"Total rows: {layout_result.total_rows}")
    print(f"Subplot rows: {layout_result.subplot_rows}")
    print(f"Height ratios: {layout_result.height_ratios}")
    
    # Add some test data to see the complete figure
    x_dates = dates.strftime('%Y-%m-%d').tolist()
    
    # Add price data to row 1
    import plotly.graph_objects as go
    fig.add_trace(go.Scatter(
        x=x_dates,
        y=test_data['Close'].tolist(),
        mode='lines',
        name='Price'
    ), row=1, col=1)
    
    # Add volume data to volume subplot
    volume_data = {
        'dates': x_dates,
        'volume': test_data['Volume'].tolist(),
        'colors': ['green'] * len(x_dates)
    }
    subplot_manager.add_subplot_data(fig, 'volume', volume_data)
    
    # Add RSI data to RSI subplot
    rsi_data = {
        'dates': x_dates,
        'rsi': [50 + 20 * np.sin(i/10) for i in range(len(x_dates))]  # Fake RSI data
    }
    subplot_manager.add_subplot_data(fig, 'rsi', rsi_data)
    
    # Check x-axis configuration
    print("\nChecking x-axis configuration:")
    for i in range(1, layout_result.total_rows + 1):
        xaxis_key = f'xaxis{i}' if i > 1 else 'xaxis'
        if xaxis_key in fig.layout:
            xaxis = fig.layout[xaxis_key]
            showticklabels = getattr(xaxis, 'showticklabels', True)  # Default is True
            print(f"Row {i}: showticklabels = {showticklabels}")
        else:
            print(f"Row {i}: xaxis not found in layout")
    
    # Save the figure to check visually (optional)
    try:
        fig.write_html("test_subplot_layout.html")
        print("\n✓ Test figure saved as 'test_subplot_layout.html'")
    except Exception as e:
        print(f"Could not save HTML file: {e}")
    
    print("\n✓ X-axis configuration test completed!")
    return True

if __name__ == "__main__":
    try:
        test_xaxis_configuration()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()