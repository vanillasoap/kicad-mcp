#!/usr/bin/env python3
"""
Test to understand pin coordinate structures in KiCad schematics
"""

import skip

def analyze_pin_coordinates():
    """Analyze how pin coordinates work in KiCad schematics."""
    print("🔍 Analyzing Pin Coordinate Structure")
    print("=" * 50)

    # Test with our simple test schematic first
    test_schematic = "test_wiring.kicad_sch"

    try:
        schem = skip.Schematic(test_schematic)
        print("✅ Test schematic loaded")
    except Exception as e:
        print(f"❌ Failed to load test schematic: {e}")
        return

    # Analyze a simple resistor component
    try:
        resistor = getattr(schem.symbol, "R_SCL", None)
        if resistor:
            print(f"\n--- Resistor (R_SCL) Analysis ---")
            print(f"Component position: {resistor.at}")
            print(f"Component lib_id: {getattr(resistor, 'lib_id', 'None')}")

            # Examine pin structure in detail
            if hasattr(resistor, 'pin') and len(resistor.pin) > 0:
                for i, pin in enumerate(resistor.pin):
                    print(f"\nPin {i+1}:")
                    print(f"  Raw pin object: {pin}")
                    print(f"  Pin type: {type(pin)}")
                    print(f"  Pin attributes: {[attr for attr in dir(pin) if not attr.startswith('_')]}")

                    # Check for coordinate attributes
                    potential_coords = ['at', 'pos', 'position', 'xy', 'x', 'y']
                    for attr in potential_coords:
                        if hasattr(pin, attr):
                            value = getattr(pin, attr)
                            print(f"  {attr}: {value}")

                    # Check if pin has raw data with coordinates
                    try:
                        if hasattr(pin, 'raw') and pin.raw:
                            print(f"  Raw data: {pin.raw}")
                    except:
                        pass

                    # For ParsedValue objects, examine all elements
                    try:
                        if hasattr(pin, '__getitem__') and hasattr(pin, '__len__'):
                            print(f"  Length: {len(pin)}")
                            for j in range(min(len(pin), 10)):  # First 10 elements
                                try:
                                    element = pin[j]
                                    print(f"  [{j}]: {element} (type: {type(element)})")
                                except:
                                    pass
                    except:
                        pass

    except Exception as e:
        print(f"❌ Error analyzing resistor: {e}")

    # Also test with production schematic
    production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"

    try:
        prod_schem = skip.Schematic(production_path)
        print(f"\n--- Production ESP32 (U3) Analysis ---")

        esp32 = getattr(prod_schem.symbol, "U3", None)
        if esp32:
            print(f"Component position: {esp32.at}")
            print(f"Component lib_id: {getattr(esp32, 'lib_id', 'None')}")

            # Look at first few pins
            if hasattr(esp32, 'pin') and len(esp32.pin) > 0:
                for i, pin in enumerate(esp32.pin[:3]):  # Just first 3 pins
                    print(f"\nESP32 Pin {i+1}:")
                    print(f"  Pin object: {pin}")
                    print(f"  Pin type: {type(pin)}")

                    # For SymbolPin objects, check coordinate attributes
                    if hasattr(pin, 'number') and hasattr(pin, 'name'):
                        print(f"  Number: {getattr(pin, 'number')}")
                        print(f"  Name: {getattr(pin, 'name')}")

                        # Check for position/coordinate attributes
                        coord_attrs = ['at', 'pos', 'position', 'xy', 'x', 'y', 'length', 'angle']
                        for attr in coord_attrs:
                            if hasattr(pin, attr):
                                value = getattr(pin, attr)
                                print(f"  {attr}: {value}")

                    # Check all attributes
                    attrs = [attr for attr in dir(pin) if not attr.startswith('_')]
                    print(f"  Available attributes: {attrs}")

    except Exception as e:
        print(f"❌ Error analyzing production schematic: {e}")

    print(f"\n💡 GOAL: Find how to calculate actual pin coordinates")
    print("Pin coordinates = Component position + Pin offset + Pin orientation")

if __name__ == "__main__":
    analyze_pin_coordinates()