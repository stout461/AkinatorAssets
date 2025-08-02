#!/usr/bin/env python3
"""
Test script to verify stock plot layout with subplots.
"""

import sys
import os
sys.path.append('src')

from stock_plotter import StockPlotter
import pandas as pd
import numpy as np

def test_stock_plot_with_subplots():
    """Test stock plot with subplots to check for layout issues."""
    
    # Create a stock plotter instance
    plotter = StockPlotter()
    
    print("Testing stock plot with volume subplot...")
    
    try:
        # Create a plot with volume subplot
        result = plotter.create_stock_plot(
            ticker='AAPL',
            period='1M',
            chart_mode='fib',
            show_volume=True,
            show_candlestick=True
        )
        
        fig = result['figure']
        
        # Check if figure has proper metadata
        if hasattr(fig, '_subplot_manager_metadata'):
            print("✓ Figure has subplot manager metadata")
            metadata = fig._subplot_manager_metadata
            layout_result = metadata['layout_result']
            
            print(f"  - Total rows: {layout_result.total_rows}")
            print(f"  - Height ratios: {layout_result.height_ratios}")
            print(f"  - Subplot rows: {layout_result.subplot_rows}")
            print(f"  - Price chart domain: {layout_result.price_chart_domain}")
            
            # Check if x-axis configuration is correct
            print("\nChecking x-axis configuration:")
            for i in range(1, layout_result.total_rows + 1):
                xaxis_key = f'xaxis{i}' if i > 1 else 'xaxis'
                if xaxis_key in fig.layout:
                    xaxis = fig.layout[xaxis_key]
                    showticklabels = getattr(xaxis, 'showticklabels', True)
                    print(f"  Row {i}: showticklabels = {showticklabels}")
            
            # Save the figure for visual inspection
            fig.write_html("test_stock_plot_layout.html")
            print("\n✓ Test figure saved as 'test_stock_plot_layout.html'")
            
        else:
            print("✗ Figure missing subplot manager metadata")
        
        print("\n✓ Stock plot layout test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stock_plot_with_subplots()
    if success:
        print("All tests passed!")
    else:
        print("Tests failed!")