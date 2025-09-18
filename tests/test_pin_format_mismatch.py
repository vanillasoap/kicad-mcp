#!/usr/bin/env python3
"""
Test to understand the pin format mismatch between discovery and connection
"""

import skip
import logging

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

def get_component_pins_debug(component):
    """Debug version showing both raw and formatted pin data."""
    pins_info = []
    try:
        if hasattr(component, 'pin'):
            for i, pin in enumerate(component.pin):
                print(f"\n--- Pin {i+1} Debug Analysis ---")

                # Raw pin data
                try:
                    raw_pin_0 = pin[0]
                    print(f"Raw pin[0]: '{raw_pin_0}' (type: {type(raw_pin_0)})")
                except Exception as e:
                    print(f"Raw pin[0] access failed: {e}")
                    raw_pin_0 = None

                # What our improved function would return
                pin_number = "Unknown"
                pin_name = None

                try:
                    # Method 1: Direct index access (most common)
                    if pin[0] is not None:
                        pin_number = str(pin[0])
                        print(f"Method 1 - Direct access: '{pin_number}'")
                except (IndexError, TypeError):
                    print("Method 1 failed, trying alternatives...")
                    # Method 2: Try accessing from raw data
                    try:
                        raw_data = getattr(pin, 'raw', None)
                        if raw_data and len(raw_data) > 1:
                            pin_number = str(raw_data[1])
                            print(f"Method 2 - Raw data: '{pin_number}'")
                    except (IndexError, TypeError, AttributeError):
                        # Method 3: Try accessing from children
                        try:
                            children = getattr(pin, 'children', None)
                            if children and len(children) > 0:
                                pin_number = str(children[0])
                                print(f"Method 3 - Children: '{pin_number}'")
                        except (IndexError, TypeError, AttributeError):
                            print("All methods failed")

                # Try to get pin name
                try:
                    if hasattr(pin, 'name') and getattr(pin, 'name', None):
                        pin_name = str(getattr(pin, 'name'))
                        print(f"Pin has name attribute: '{pin_name}'")
                    elif len(pin) > 2:
                        potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                        if potential_name:
                            pin_name = str(potential_name)
                            print(f"Pin name from pin[2]: '{pin_name}'")
                except (IndexError, TypeError, AttributeError):
                    print("No pin name found")

                # Handle edge cases
                if not pin_number or pin_number.strip() == "":
                    pin_number = "Unknown"

                # Final formatted result (what get_component_pins would return)
                final_pin_number = pin_number.strip()
                final_pin_name = pin_name.strip() if pin_name else None

                print(f"Final pin number: '{final_pin_number}'")
                print(f"Final pin name: '{final_pin_name}'")

                # What would be displayed to user
                if final_pin_name and final_pin_name != final_pin_number:
                    display_format = f"{final_pin_number} ({final_pin_name})"
                else:
                    display_format = final_pin_number
                print(f"Display format: '{display_format}'")

                pin_info = {
                    "number": final_pin_number,
                    "name": final_pin_name,
                    "display": display_format,
                    "raw_pin_0": str(raw_pin_0) if raw_pin_0 is not None else None,
                    "uuid": safe_serialize(getattr(pin, "uuid", None))
                }
                pins_info.append(pin_info)

                # Test wire connection matching
                print(f"\n--- Wire Connection Matching Test ---")
                test_pins = [final_pin_number, display_format]
                if final_pin_name:
                    test_pins.append(final_pin_name)

                for test_pin in test_pins:
                    # Simulate the wire connection matching logic
                    matches = test_wire_connection_matching(pin, test_pin)
                    print(f"  '{test_pin}' -> {matches}")

    except Exception as e:
        logging.warning(f"Could not enumerate pins for component: {e}")

    return {
        "pin_count": len(pins_info),
        "pins": pins_info
    }

def test_wire_connection_matching(pin_obj, requested_pin):
    """Test the wire connection matching logic."""
    try:
        # Get the raw pin number from the pin object (what wire connection uses)
        pin_number = str(pin_obj[0]) if pin_obj[0] is not None else ""

        # Method 1: Direct exact match
        if pin_number == requested_pin:
            return "✅ Direct match"

        # Method 2: Number part extraction
        if pin_number and requested_pin:
            number_part = pin_number.split()[0] if " " in pin_number else pin_number
            if number_part == requested_pin:
                return "✅ Number part match"

        # Method 3: Name matching
        if len(pin_obj) > 2:
            potential_name = pin_obj[2] if pin_obj[2] != getattr(pin_obj, 'uuid', None) else None
            if potential_name:
                name_str = str(potential_name)
                if name_str == requested_pin:
                    return "✅ Name match"
                elif "/" in name_str and requested_pin in name_str.split("/"):
                    return "✅ GPIO name part match"

        return "❌ No match"

    except Exception as e:
        return f"❌ Error: {e}"

def test_pin_format_analysis():
    """Test pin format analysis on the test schematic."""
    print("🔍 Pin Format Mismatch Analysis")
    print("=" * 50)

    schem = skip.Schematic('test_wiring.kicad_sch')

    components_to_test = ['R_SCL', 'U1']

    for comp_name in components_to_test:
        print(f"\n🔧 Analyzing {comp_name}:")
        comp = getattr(schem.symbol, comp_name, None)

        if comp:
            pins_result = get_component_pins_debug(comp)
            print(f"\n📊 Summary for {comp_name}:")
            print(f"  Total pins: {pins_result['pin_count']}")

            for pin in pins_result['pins']:
                print(f"  Pin: {pin['display']} (raw: {pin['raw_pin_0']})")
        else:
            print(f"  Component {comp_name} not found")

if __name__ == "__main__":
    test_pin_format_analysis()