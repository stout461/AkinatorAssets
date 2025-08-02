#!/usr/bin/env python3
"""
Test script for the subplot configuration validation function only.
"""

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


def test_subplot_config_validation():
    """Test the subplot configuration validation function."""
    print("Testing subplot configuration validation...")
    
    # Test valid configuration
    valid_config = {
        "subplots": ["volume", "rsi"],
        "graph_settings": {
            "show_candlestick": True,
            "show_graph_lines": True,
            "show_time_selector": False
        },
        "layout_preferences": {
            "max_subplots": 3,
            "min_price_height": 0.4
        }
    }
    
    errors = _validate_subplot_config_structure(valid_config)
    assert len(errors) == 0, f"Valid config should have no errors, got: {errors}"
    print("✅ Valid configuration passed validation")
    
    # Test invalid configuration - missing subplots
    invalid_config1 = {
        "graph_settings": {
            "show_candlestick": True
        }
    }
    
    errors = _validate_subplot_config_structure(invalid_config1)
    assert len(errors) > 0, "Missing subplots should cause validation error"
    assert any("Missing required field 'subplots'" in error['message'] for error in errors)
    print("✅ Missing subplots field correctly detected")
    
    # Test invalid configuration - wrong data types
    invalid_config2 = {
        "subplots": "not_an_array",
        "graph_settings": {
            "show_candlestick": "not_a_boolean"
        }
    }
    
    errors = _validate_subplot_config_structure(invalid_config2)
    assert len(errors) >= 2, "Multiple validation errors should be detected"
    print("✅ Data type validation working correctly")
    
    # Test invalid configuration - unknown graph settings
    invalid_config3 = {
        "subplots": ["volume"],
        "graph_settings": {
            "unknown_setting": True
        }
    }
    
    errors = _validate_subplot_config_structure(invalid_config3)
    assert len(errors) > 0, "Unknown graph setting should cause validation error"
    assert any("Unknown graph setting" in error['message'] for error in errors)
    print("✅ Unknown graph settings correctly detected")
    
    # Test empty subplots array
    empty_config = {
        "subplots": []
    }
    
    errors = _validate_subplot_config_structure(empty_config)
    assert len(errors) == 0, "Empty subplots array should be valid"
    print("✅ Empty subplots array handled correctly")
    
    # Test invalid layout preferences
    invalid_layout_config = {
        "subplots": ["volume"],
        "layout_preferences": {
            "max_subplots": 15,  # Too high
            "min_price_height": 1.5  # Too high
        }
    }
    
    errors = _validate_subplot_config_structure(invalid_layout_config)
    assert len(errors) >= 2, "Invalid layout preferences should cause validation errors"
    print("✅ Layout preferences validation working correctly")
    
    print("All validation tests passed! ✅")


def main():
    """Run validation tests."""
    print("🧪 Testing subplot configuration validation...")
    print("=" * 50)
    
    try:
        test_subplot_config_validation()
        
        print("\n" + "=" * 50)
        print("🎉 Validation tests passed successfully!")
        print("\nThe validation function correctly handles:")
        print("✅ Valid configurations")
        print("✅ Missing required fields")
        print("✅ Wrong data types")
        print("✅ Unknown settings")
        print("✅ Invalid ranges for numeric values")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)