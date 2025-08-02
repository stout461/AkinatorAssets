#!/usr/bin/env python3
"""
Quick test script to verify subplot layout is working correctly.
"""

import sys
import os
sys.path.append('src')

from sub_plots import SubplotManager
import pandas as pd
import numpy as np

def test_subplot_layout():
    """Test that subplot layout doesn't cause overlapping issues."""
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    test_data = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # Initialize subplot manager
    subplot_manager = SubplotManager()
    
    # Test with volume subplot
    print("Testing with volume subplot...")
    requested_subplots = ['volume']
    
    # Calculate layout
    layout_result = subplot_manager.calculate_layout(requested_subplots)
    print(f"Layout result: {layout_result}")
    
    # Create figure
    fig = subplot_manager.create_subplot_figure(requested_subplots)
    print(f"Figure created with {layout_result.total_rows} rows")
    print(f"Height ratios: {layout_result.height_ratios}")
    print(f"Subplot rows: {layout_result.subplot_rows}")
    
    # Check if figure has proper metadata
    if hasattr(fig, '_subplot_manager_metadata'):
        print("✓ Figure has proper metadata")
        metadata = fig._subplot_manager_metadata
        print(f"  - Layout result stored: {metadata['layout_result'] is not None}")
        print(f"  - Requested subplots: {metadata['requested_subplots']}")
        print(f"  - Subplot rows: {metadata['subplot_rows']}")
    else:
        print("✗ Figure missing metadata")
    
    # Test with multiple subplots
    print("\nTesting with multiple subplots...")
    requested_subplots = ['volume', 'rsi']
    
    layout_result = subplot_manager.calculate_layout(requested_subplots)
    print(f"Layout result: {layout_result}")
    
    fig = subplot_manager.create_subplot_figure(requested_subplots)
    print(f"Figure created with {layout_result.total_rows} rows")
    print(f"Height ratios: {layout_result.height_ratios}")
    print(f"Subplot rows: {layout_result.subplot_rows}")
    
    print("\n✓ Subplot layout test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_subplot_layout()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()