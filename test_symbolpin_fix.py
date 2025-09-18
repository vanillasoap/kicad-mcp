#!/usr/bin/env python3
"""
Test the SymbolPin fix with the production schematic
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

def get_component_pins_fixed(component):
    """Fixed version that handles both SymbolPin and ParsedValue objects."""
    pins_info = []
    try:
        if hasattr(component, 'pin'):
            for pin in component.pin:
                pin_number = "Unknown"
                pin_name = None

                try:
                    # Method 1: SymbolPin objects (newer format)
                    if hasattr(pin, 'number') and hasattr(pin, 'name'):
                        pin_number = str(getattr(pin, 'number'))
                        pin_name_attr = getattr(pin, 'name', None)
                        if pin_name_attr and str(pin_name_attr).strip() != "~":
                            pin_name = str(pin_name_attr)

                    # Method 2: ParsedValue objects (older format) - Direct index access
                    elif hasattr(pin, '__getitem__'):
                        try:
                            if pin[0] is not None:
                                pin_number = str(pin[0])
                                # Try to get name from pin[2] if available
                                if len(pin) > 2:
                                    potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                                    if potential_name and str(potential_name).strip() != "~":
                                        pin_name = str(potential_name)
                        except (IndexError, TypeError):
                            pass

                    # Method 3: Fallback - Try accessing from raw data
                    if pin_number == "Unknown":
                        try:
                            raw_data = getattr(pin, 'raw', None)
                            if raw_data and len(raw_data) > 1:
                                pin_number = str(raw_data[1])
                        except (IndexError, TypeError, AttributeError):
                            # Method 4: Try accessing from children
                            try:
                                children = getattr(pin, 'children', None)
                                if children and len(children) > 0:
                                    pin_number = str(children[0])
                            except (IndexError, TypeError, AttributeError):
                                pass

                except Exception as e:
                    logging.debug(f"Error extracting pin data: {e}")

                # Handle edge cases where pin number might be empty or whitespace
                if not pin_number or pin_number.strip() == "":
                    pin_number = "Unknown"

                pin_info = {
                    "number": pin_number.strip(),
                    "name": pin_name.strip() if pin_name else None,
                    "uuid": safe_serialize(getattr(pin, "uuid", None))
                }
                pins_info.append(pin_info)
    except Exception as e:
        logging.warning(f"Could not enumerate pins for component: {e}")

    return {
        "pin_count": len(pins_info),
        "pins": pins_info
    }

def test_pin_matching_fixed(component, requested_pin):
    """Test the fixed pin matching logic."""
    if not hasattr(component, 'pin'):
        return False

    for pin in component.pin:
        try:
            pin_number = ""
            pin_name = ""

            # Extract pin number and name based on pin object type
            if hasattr(pin, 'number') and hasattr(pin, 'name'):
                # SymbolPin objects (newer format)
                pin_number = str(getattr(pin, 'number'))
                pin_name_attr = getattr(pin, 'name', None)
                if pin_name_attr:
                    pin_name = str(pin_name_attr)
            elif hasattr(pin, '__getitem__'):
                # ParsedValue objects (older format)
                try:
                    pin_number = str(pin[0]) if pin[0] is not None else ""
                    if len(pin) > 2:
                        potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                        if potential_name:
                            pin_name = str(potential_name)
                except (IndexError, TypeError):
                    pass

            # Method 1: Direct exact match with pin number
            if pin_number == requested_pin:
                return True

            # Method 2: Check if requested pin matches the number part of formatted pins
            elif pin_number and requested_pin:
                number_part = pin_number.split()[0] if " " in pin_number else pin_number
                if number_part == requested_pin:
                    return True

            # Method 3: Check if user provided a GPIO name that matches the description
            if pin_name:
                # Direct name match
                if pin_name == requested_pin:
                    return True
                # Check if the requested pin is part of the GPIO name (e.g., "GPIO21" from "GPIO21/ADC")
                elif "/" in pin_name and requested_pin in pin_name.split("/"):
                    return True

        except (IndexError, TypeError):
            continue

    return False

def test_symbolpin_fix():
    """Test the SymbolPin fix with the production schematic."""
    print("🔧 Testing SymbolPin Fix with Production Schematic")
    print("=" * 60)

    schematic_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"

    try:
        schem = skip.Schematic(schematic_path)
        print("✅ Schematic loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load schematic: {e}")
        return

    # Test components from your report
    test_cases = [
        ("U3", "ESP32 module", ["16", "23", "28", "GPIO15", "GPIO21", "CHIP_PU"]),
        ("R_SCL", "Pull-up resistor", ["1", "2"]),
        ("U1", "TAS5830", ["10", "25", "26"]),
    ]

    for comp_name, description, test_pins in test_cases:
        print(f"\n--- {comp_name} ({description}) ---")

        try:
            comp = getattr(schem.symbol, comp_name, None)
            if not comp:
                print(f"❌ Component {comp_name} not found")
                continue

            # Test pin discovery
            pins_result = get_component_pins_fixed(comp)
            print(f"📌 Pin discovery: {pins_result['pin_count']} pins found")

            # Show sample pins
            print("Sample pins:")
            for pin in pins_result['pins'][:5]:
                if pin['name']:
                    display = f"{pin['number']} ({pin['name']})"
                else:
                    display = pin['number']
                print(f"  {display}")

            if pins_result['pin_count'] > 5:
                print(f"  ... and {pins_result['pin_count'] - 5} more")

            # Test pin matching
            print(f"\n🔍 Pin matching tests for {comp_name}:")
            for test_pin in test_pins:
                found = test_pin_matching_fixed(comp, test_pin)
                status = "✅" if found else "❌"
                print(f"  '{test_pin}' -> {status}")

        except Exception as e:
            print(f"❌ Error testing {comp_name}: {e}")

    print(f"\n🎯 EXPECTED RESULTS AFTER SERVER RESTART:")
    print("✅ ESP32 pin '23' should match SymbolPin 23 'GPIO21/ADC'")
    print("✅ ESP32 pin 'GPIO21' should match SymbolPin 23 'GPIO21/ADC'")
    print("✅ Resistor pin '1' should match SymbolPin 1 '~'")
    print("✅ TAS5830 pins should continue working as before")

if __name__ == "__main__":
    test_symbolpin_fix()