#!/usr/bin/env python3
"""
Test script to verify the domain fix prevents main chart bleeding.
"""

import sys
import os
sys.path.append('src')

def test_domain_configuration():
    """Test that domains are correctly configured to prevent bleeding."""
    
    try:
        from sub_plots import SubplotManager
        import plotly.graph_objects as go
        
        # Initialize subplot manager
        subplot_manager = SubplotManager()
        
        # Test with volume subplot
        requested_subplots = ['volume']
        
        # Create figure
        fig = subplot_manager.create_subplot_figure(requested_subplots)
        layout_result = fig._subplot_manager_metadata['layout_result']
        
        print("=== Domain Configuration Test ===")
        print(f"Height ratios: {layout_result.height_ratios}")
        print(f"Subplot rows: {layout_result.subplot_rows}")
        
        # Check domain configuration
        print("\nDomain Configuration:")
        
        # Check price chart domain (row 1)
        if 'xaxis' in fig.layout and hasattr(fig.layout.yaxis, 'domain'):
            price_domain = fig.layout.yaxis.domain
            print(f"Price chart (Row 1): domain = {price_domain}")
        else:
            print("Price chart (Row 1): domain not found")
        
        # Check volume subplot domain (row 2)
        if 'yaxis2' in fig.layout and hasattr(fig.layout.yaxis2, 'domain'):
            volume_domain = fig.layout.yaxis2.domain
            print(f"Volume subplot (Row 2): domain = {volume_domain}")
        else:
            print("Volume subplot (Row 2): domain not found")
        
        # Verify no overlap
        if hasattr(fig.layout.yaxis, 'domain') and hasattr(fig.layout.yaxis2, 'domain'):
            price_domain = fig.layout.yaxis.domain
            volume_domain = fig.layout.yaxis2.domain
            
            price_start, price_end = price_domain
            volume_start, volume_end = volume_domain
            
            print(f"\nOverlap Check:")
            print(f"Price: [{price_start}, {price_end}]")
            print(f"Volume: [{volume_start}, {volume_end}]")
            
            # Check if domains overlap
            if price_start >= volume_end:
                print("✅ No overlap - domains are properly separated!")
            else:
                print("❌ Overlap detected - domains are not properly separated!")
        
        return True
        
    except Exception as e:
        print(f"✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_domain_configuration()
    if success:
        print("\n✅ Domain configuration test completed!")
    else:
        print("\n❌ Domain configuration test failed!")