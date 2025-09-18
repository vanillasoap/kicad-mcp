#!/usr/bin/env python3
"""
Comprehensive pin debugging tool to identify "Unknown" pin issues
"""

import skip
import logging
import sys
import os

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

def deep_pin_analysis(pin, pin_index):
    """Perform deep analysis of a pin object to understand its structure."""
    analysis = {
        'index': pin_index,
        'pin_object': str(pin),
        'pin_type': str(type(pin)),
        'access_methods': {},
        'potential_issues': []
    }

    # Test Method 1: Direct index access
    try:
        pin_0 = pin[0]
        analysis['access_methods']['pin[0]'] = {
            'value': str(pin_0),
            'type': str(type(pin_0)),
            'is_none': pin_0 is None,
            'is_empty': str(pin_0).strip() == "" if pin_0 is not None else True,
            'success': True
        }

        if pin_0 is None:
            analysis['potential_issues'].append("pin[0] is None")
        elif str(pin_0).strip() == "":
            analysis['potential_issues'].append("pin[0] is empty string or whitespace")

    except Exception as e:
        analysis['access_methods']['pin[0]'] = {
            'error': str(e),
            'success': False
        }
        analysis['potential_issues'].append(f"pin[0] access failed: {e}")

    # Test Method 2: Raw data access
    try:
        raw_data = getattr(pin, 'raw', None)
        if raw_data:
            analysis['access_methods']['raw'] = {
                'data': str(raw_data),
                'length': len(raw_data),
                'success': True
            }
            if len(raw_data) > 1:
                analysis['access_methods']['raw']['pin_identifier'] = str(raw_data[1])
        else:
            analysis['access_methods']['raw'] = {'data': 'None', 'success': False}
    except Exception as e:
        analysis['access_methods']['raw'] = {'error': str(e), 'success': False}

    # Test Method 3: Children access
    try:
        children = getattr(pin, 'children', None)
        if children:
            analysis['access_methods']['children'] = {
                'data': str(children),
                'length': len(children),
                'success': True
            }
            if len(children) > 0:
                analysis['access_methods']['children']['first_child'] = str(children[0])
        else:
            analysis['access_methods']['children'] = {'data': 'None', 'success': False}
    except Exception as e:
        analysis['access_methods']['children'] = {'error': str(e), 'success': False}

    # Test Method 4: Length and indexing
    try:
        pin_length = len(pin)
        analysis['access_methods']['length'] = {
            'value': pin_length,
            'success': True
        }

        # Try to access additional indices
        if pin_length > 1:
            analysis['access_methods']['additional_indices'] = {}
            for i in range(1, min(pin_length, 5)):
                try:
                    analysis['access_methods']['additional_indices'][f'pin[{i}]'] = str(pin[i])
                except Exception as e:
                    analysis['access_methods']['additional_indices'][f'pin[{i}]'] = f"Error: {e}"

    except Exception as e:
        analysis['access_methods']['length'] = {'error': str(e), 'success': False}

    return analysis

def analyze_component_pins(component, component_name):
    """Analyze all pins of a component for debugging."""
    print(f"\n=== Deep Analysis: {component_name} ===")
    print(f"Component type: {type(component)}")
    print(f"Has pin attribute: {hasattr(component, 'pin')}")

    if not hasattr(component, 'pin'):
        print("❌ Component has no 'pin' attribute")
        return

    pin_list = component.pin
    print(f"Pin list type: {type(pin_list)}")
    print(f"Pin count: {len(pin_list)}")

    if len(pin_list) == 0:
        print("❌ Component has no pins")
        return

    # Analyze first few pins in detail
    analysis_results = []
    for i, pin in enumerate(pin_list[:3]):  # Analyze first 3 pins
        print(f"\n--- Pin {i+1} Analysis ---")
        pin_analysis = deep_pin_analysis(pin, i)
        analysis_results.append(pin_analysis)

        print(f"Pin object: {pin_analysis['pin_object']}")
        print(f"Pin type: {pin_analysis['pin_type']}")

        # Check access methods
        for method, result in pin_analysis['access_methods'].items():
            if result.get('success', False):
                print(f"✅ {method}: {result}")
            else:
                print(f"❌ {method}: {result}")

        # Report potential issues
        if pin_analysis['potential_issues']:
            print("⚠️  Potential issues:")
            for issue in pin_analysis['potential_issues']:
                print(f"   - {issue}")

        # Determine what our pin discovery would return
        predicted_result = predict_pin_discovery_result(pin_analysis)
        print(f"🔍 Predicted pin discovery result: '{predicted_result}'")

    return analysis_results

def predict_pin_discovery_result(pin_analysis):
    """Predict what the pin discovery function would return for this pin."""
    # Follow the same logic as our improved pin discovery function

    # Method 1: Direct index access
    pin_0_result = pin_analysis['access_methods'].get('pin[0]', {})
    if pin_0_result.get('success') and not pin_0_result.get('is_none') and not pin_0_result.get('is_empty'):
        return pin_0_result['value']

    # Method 2: Raw data access
    raw_result = pin_analysis['access_methods'].get('raw', {})
    if raw_result.get('success') and 'pin_identifier' in raw_result:
        return raw_result['pin_identifier']

    # Method 3: Children access
    children_result = pin_analysis['access_methods'].get('children', {})
    if children_result.get('success') and 'first_child' in children_result:
        return children_result['first_child']

    # If all methods fail
    return "Unknown"

def debug_schematic_pins(schematic_path):
    """Debug pin issues in a schematic file."""
    print(f"🔍 Debugging pin issues in: {schematic_path}")

    if not os.path.exists(schematic_path):
        print(f"❌ Schematic file not found: {schematic_path}")
        return

    try:
        schem = skip.Schematic(schematic_path)
        print(f"✅ Schematic loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load schematic: {e}")
        return

    # Get all components
    available_components = [attr for attr in dir(schem.symbol) if not attr.startswith('_')]
    print(f"📊 Found {len(available_components)} components: {available_components}")

    # Analyze each component
    summary = {'total_components': len(available_components), 'problematic_components': []}

    for comp_name in available_components:
        try:
            comp = getattr(schem.symbol, comp_name)

            # Quick check for "Unknown" pins
            pin_count = len(comp.pin) if hasattr(comp, 'pin') else 0
            unknown_count = 0

            if hasattr(comp, 'pin'):
                for pin in comp.pin:
                    try:
                        pin_value = pin[0]
                        if pin_value is None or str(pin_value).strip() == "":
                            unknown_count += 1
                    except:
                        unknown_count += 1

            print(f"\n{comp_name}: {pin_count} pins, {unknown_count} potentially 'Unknown'")

            if unknown_count > 0:
                summary['problematic_components'].append({
                    'name': comp_name,
                    'total_pins': pin_count,
                    'unknown_pins': unknown_count
                })

                # Deep analysis for problematic components
                analyze_component_pins(comp, comp_name)

        except Exception as e:
            print(f"❌ Error analyzing {comp_name}: {e}")
            summary['problematic_components'].append({
                'name': comp_name,
                'error': str(e)
            })

    # Summary report
    print(f"\n=== DEBUGGING SUMMARY ===")
    print(f"Total components analyzed: {summary['total_components']}")
    print(f"Problematic components: {len(summary['problematic_components'])}")

    if summary['problematic_components']:
        print("\nComponents with potential 'Unknown' pin issues:")
        for comp in summary['problematic_components']:
            if 'error' in comp:
                print(f"  ❌ {comp['name']}: {comp['error']}")
            else:
                print(f"  ⚠️  {comp['name']}: {comp['unknown_pins']}/{comp['total_pins']} pins potentially 'Unknown'")
    else:
        print("✅ No obvious pin issues found with this schematic")

    return summary

def main():
    """Main debugging function."""
    if len(sys.argv) > 1:
        schematic_path = sys.argv[1]
    else:
        # Default to test schematic
        schematic_path = "test_wiring.kicad_sch"

    print("🔧 KiCad MCP Pin Debugging Tool")
    print("=" * 50)

    debug_schematic_pins(schematic_path)

    print("\n💡 RECOMMENDATIONS:")
    print("1. If pins show as 'Unknown', check the symbol library used")
    print("2. Verify the schematic file is not corrupted")
    print("3. Check if components are multi-unit symbols")
    print("4. Consider regenerating symbols from the library")

if __name__ == "__main__":
    main()