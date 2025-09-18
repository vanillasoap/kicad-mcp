#!/usr/bin/env python3
"""
Research symbol library access for pin coordinate calculation
"""

import skip

def research_symbol_library_access():
    """Research how to access symbol library information for pin coordinates."""
    print("📚 Researching Symbol Library Access for Pin Coordinates")
    print("=" * 65)

    try:
        production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
        schem = skip.Schematic(production_path)

        esp32 = getattr(schem.symbol, "U3", None)
        tas5830 = getattr(schem.symbol, "U1", None)

        if not esp32 or not tas5830:
            print("❌ Components not found")
            return

        print("--- Component Library References ---")
        print(f"ESP32 lib_id: {getattr(esp32, 'lib_id', 'None')}")
        print(f"TAS5830 lib_id: {getattr(tas5830, 'lib_id', 'None')}")

        # Check if components have symbol definitions
        print(f"\n--- Symbol Definition Access ---")

        # Check ESP32 symbol attributes
        print(f"ESP32 attributes: {[attr for attr in dir(esp32) if not attr.startswith('_')]}")

        # Check if we can access symbol definition
        if hasattr(esp32, 'symbol'):
            print(f"ESP32 symbol: {esp32.symbol}")
        if hasattr(esp32, 'lib_symbols'):
            print(f"ESP32 lib_symbols: {esp32.lib_symbols}")

        print(f"\nTAS5830 attributes: {[attr for attr in dir(tas5830) if not attr.startswith('_')]}")

        if hasattr(tas5830, 'symbol'):
            print(f"TAS5830 symbol: {tas5830.symbol}")
        if hasattr(tas5830, 'lib_symbols'):
            print(f"TAS5830 lib_symbols: {tas5830.lib_symbols}")

        # Check if schematic has library access
        print(f"\n--- Schematic Library Access ---")
        schematic_attrs = [attr for attr in dir(schem) if not attr.startswith('_')]
        print(f"Schematic attributes: {schematic_attrs}")

        if hasattr(schem, 'lib_symbols'):
            print(f"Schematic lib_symbols: {schem.lib_symbols}")
        if hasattr(schem, 'symbol_lib'):
            print(f"Schematic symbol_lib: {schem.symbol_lib}")

        # Try to understand pin coordinate patterns
        print(f"\n--- Pin Coordinate Pattern Analysis ---")

        # Get working ESP32 pins to understand pattern
        esp32_pins = []
        if hasattr(esp32, 'pin'):
            for pin in esp32.pin:
                if hasattr(pin, 'number') and hasattr(pin, 'location'):
                    number = getattr(pin, 'number')
                    location = pin.location.value[:2] if hasattr(pin.location, 'value') else None
                    esp32_pins.append((number, location))
                if len(esp32_pins) >= 5:  # First 5 pins
                    break

        print(f"ESP32 pin samples: {esp32_pins}")

        # Analyze ESP32 component position and pin offsets
        esp32_center = esp32.at.value[:2] if hasattr(esp32.at, 'value') else [float(esp32.at[0]), float(esp32.at[1])]
        print(f"ESP32 center: {esp32_center}")

        if esp32_pins:
            print("ESP32 pin offsets from center:")
            for number, location in esp32_pins[:3]:
                if location:
                    offset_x = location[0] - esp32_center[0]
                    offset_y = location[1] - esp32_center[1]
                    print(f"  Pin {number}: offset ({offset_x:.2f}, {offset_y:.2f})")

        # Try to determine TAS5830 package type
        print(f"\n--- TAS5830 Package Analysis ---")
        tas5830_center = tas5830.at.value[:2] if hasattr(tas5830.at, 'value') else [float(tas5830.at[0]), float(tas5830.at[1])]
        print(f"TAS5830 center: {tas5830_center}")

        # Check if TAS5830 has any geometric information
        if hasattr(tas5830, 'property'):
            print(f"TAS5830 properties:")
            for prop in tas5830.property:
                try:
                    if hasattr(prop, 'key') and hasattr(prop, 'value'):
                        key = getattr(prop, 'key')
                        value = getattr(prop, 'value')
                        print(f"  {key}: {value}")
                except:
                    pass

        # Try to estimate TAS5830 pin positions based on common IC packages
        print(f"\n--- Attempting TAS5830 Pin Position Estimation ---")

        # Common TSSOP/QFNP/BGA packages have predictable pin layouts
        # Let's see if we can determine the package type and estimate positions

        tas5830_lib_id = getattr(tas5830, 'lib_id', None)
        if tas5830_lib_id:
            lib_id_str = str(tas5830_lib_id)
            print(f"TAS5830 lib_id analysis: {lib_id_str}")

            # Look for package clues in the lib_id
            package_clues = ['TSSOP', 'QFN', 'BGA', 'LQFP', 'SOIC', 'DIP']
            detected_package = None
            for package in package_clues:
                if package.lower() in lib_id_str.lower():
                    detected_package = package
                    break

            if detected_package:
                print(f"📦 Detected package type: {detected_package}")
            else:
                print(f"❓ Package type not detected from lib_id")

        # Test a simple geometric estimation
        print(f"\n--- Testing Geometric Pin Estimation ---")

        # For demonstration, assume TAS5830 is a standard IC with pins on sides
        # This is a fallback method when symbol library data isn't available

        def estimate_ic_pin_position(component_center, pin_number, total_pins=32, package_width=7.0, package_height=7.0):
            """Estimate pin position for standard IC packages."""
            center_x, center_y = component_center
            pin_num = int(pin_number)

            # Simple quadrant-based estimation for quad package
            pins_per_side = total_pins // 4
            pin_spacing = 0.65  # mm, typical for TSSOP

            if pin_num <= pins_per_side:
                # Bottom side (pins 1-8)
                x = center_x - (package_width/2) + (pin_num - 1) * pin_spacing
                y = center_y - (package_height/2)
            elif pin_num <= pins_per_side * 2:
                # Right side (pins 9-16)
                x = center_x + (package_width/2)
                y = center_y - (package_height/2) + (pin_num - pins_per_side - 1) * pin_spacing
            elif pin_num <= pins_per_side * 3:
                # Top side (pins 17-24)
                x = center_x + (package_width/2) - (pin_num - pins_per_side * 2 - 1) * pin_spacing
                y = center_y + (package_height/2)
            else:
                # Left side (pins 25-32)
                x = center_x - (package_width/2)
                y = center_y + (package_height/2) - (pin_num - pins_per_side * 3 - 1) * pin_spacing

            return [x, y]

        # Test estimation on a few TAS5830 pins
        test_pins = ['8', '10', '25', '26']
        for pin_num in test_pins:
            estimated_pos = estimate_ic_pin_position(tas5830_center, pin_num)
            print(f"Pin {pin_num} estimated position: {estimated_pos}")

    except Exception as e:
        print(f"❌ Research failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    research_symbol_library_access()