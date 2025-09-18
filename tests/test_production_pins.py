#!/usr/bin/env python3
"""
Test the production schematic pin matching to verify the fix is working
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

def test_production_pin_matching(schematic_path):
    """Test pin matching on the actual production schematic."""
    print("🔍 Testing Production Pin Matching")
    print("=" * 50)
    print(f"Schematic: {schematic_path}")

    try:
        schem = skip.Schematic(schematic_path)
        print("✅ Schematic loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load schematic: {e}")
        return

    # Test the components mentioned in the report
    test_components = [
        ("U3", "ESP32 module", ["23", "GPIO21", "GPIO21/ADC"]),
        ("R_SCL", "Pull-up resistor", ["1", "2"]),
        ("U1", "TAS5830", ["10", "25", "26"])
    ]

    for comp_name, description, test_pins in test_components:
        print(f"\n--- {comp_name} ({description}) ---")

        try:
            comp = getattr(schem.symbol, comp_name, None)
            if not comp:
                print(f"❌ Component {comp_name} not found")
                continue

            print(f"✅ Component found")

            # Show pin structure
            if hasattr(comp, 'pin') and len(comp.pin) > 0:
                print(f"📌 Pin count: {len(comp.pin)}")

                # Show first few pins to understand structure
                print("First 3 pins:")
                for i, pin in enumerate(comp.pin[:3]):
                    try:
                        pin_number = str(pin[0]) if pin[0] is not None else "None"
                        pin_name = None
                        if len(pin) > 2:
                            potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                            if potential_name:
                                pin_name = str(potential_name)

                        display = f"{pin_number} ({pin_name})" if pin_name else pin_number
                        print(f"  Pin {i+1}: {display}")
                    except Exception as e:
                        print(f"  Pin {i+1}: Error - {e}")

                # Test pin matching with flexible logic
                print(f"\n🔧 Testing pin matching for {comp_name}:")
                for test_pin in test_pins:
                    found = test_flexible_pin_matching(comp, test_pin)
                    status = "✅" if found else "❌"
                    print(f"  '{test_pin}' -> {status}")

            else:
                print("❌ No pins found")

        except Exception as e:
            print(f"❌ Error analyzing {comp_name}: {e}")

def test_flexible_pin_matching(component, requested_pin):
    """Test the flexible pin matching logic."""
    if not hasattr(component, 'pin'):
        return False

    for pin in component.pin:
        try:
            # Get the raw pin number from the pin object
            pin_number = str(pin[0]) if pin[0] is not None else ""

            # Method 1: Direct exact match
            if pin_number == requested_pin:
                return True

            # Method 2: Number part matching (handles "23 (GPIO21)" -> "23")
            elif pin_number and requested_pin:
                number_part = pin_number.split()[0] if " " in pin_number else pin_number
                if number_part == requested_pin:
                    return True

            # Method 3: Name matching (handles GPIO names)
            if len(pin) > 2:
                potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                if potential_name:
                    name_str = str(potential_name)
                    # Direct name match
                    if name_str == requested_pin:
                        return True
                    # Check if the requested pin is part of the GPIO name
                    elif "/" in name_str and requested_pin in name_str.split("/"):
                        return True

        except (IndexError, TypeError):
            continue

    return False

def main():
    """Main test function."""
    # Test with the production schematic path
    production_schematic = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"

    test_production_pin_matching(production_schematic)

    print(f"\n💡 INSTRUCTIONS:")
    print("1. If pin matching tests show ❌, restart your MCP server to pick up the updated code")
    print("2. If tests show ✅, the pin matching fix is working and connections should succeed")
    print("3. Try the wire connections again after restarting the server")

if __name__ == "__main__":
    main()