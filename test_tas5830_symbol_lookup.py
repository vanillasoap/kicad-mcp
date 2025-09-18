#!/usr/bin/env python3
"""
Look up TAS5830 symbol definition from library to get pin coordinates
"""

import skip

def lookup_tas5830_symbol_pins():
    """Look up TAS5830 symbol from library to get actual pin coordinates."""
    print("📖 TAS5830 Symbol Library Lookup")
    print("=" * 50)

    try:
        production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
        schem = skip.Schematic(production_path)

        tas5830 = getattr(schem.symbol, "U1", None)
        if not tas5830:
            print("❌ TAS5830 component not found")
            return

        tas5830_lib_id = getattr(tas5830, 'lib_id', None)
        print(f"TAS5830 lib_id: {tas5830_lib_id}")

        # Search for TAS5830 symbol in library
        if hasattr(schem, 'lib_symbols'):
            print(f"\n🔍 Searching for TAS5830 symbol in library...")

            tas5830_symbol = None
            for symbol in schem.lib_symbols:
                try:
                    symbol_name = str(symbol).split("'")[1] if "'" in str(symbol) else str(symbol)
                    print(f"  Found symbol: {symbol_name}")

                    if 'TAS5830' in symbol_name or 'tas5830' in symbol_name.lower():
                        tas5830_symbol = symbol
                        print(f"  ✅ Found TAS5830 symbol: {symbol}")
                        break
                except Exception as e:
                    continue

            if tas5830_symbol:
                print(f"\n📋 TAS5830 Symbol Analysis:")
                print(f"Symbol object: {tas5830_symbol}")

                # Get symbol attributes
                symbol_attrs = [attr for attr in dir(tas5830_symbol) if not attr.startswith('_')]
                print(f"Symbol attributes: {symbol_attrs}")

                # Look for pins in the symbol definition
                if hasattr(tas5830_symbol, 'pin'):
                    print(f"\n📌 TAS5830 Symbol Pins:")
                    pin_count = 0
                    for pin in tas5830_symbol.pin:
                        pin_count += 1
                        if pin_count > 10:  # Just show first 10 pins
                            print(f"  ... and more pins")
                            break

                        print(f"\nSymbol Pin {pin_count}:")
                        print(f"  Object: {pin}")
                        print(f"  Type: {type(pin)}")

                        # Get pin attributes
                        pin_attrs = [attr for attr in dir(pin) if not attr.startswith('_')]
                        print(f"  Attributes: {pin_attrs}")

                        # Extract pin information
                        if hasattr(pin, 'number'):
                            pin_number = getattr(pin, 'number')
                            print(f"  Number: {pin_number}")

                        if hasattr(pin, 'name'):
                            pin_name = getattr(pin, 'name')
                            print(f"  Name: {pin_name}")

                        if hasattr(pin, 'at'):
                            pin_at = getattr(pin, 'at')
                            print(f"  Position (at): {pin_at}")
                            if hasattr(pin_at, 'value'):
                                pin_coords = pin_at.value
                                print(f"  ✅ Symbol Pin Coordinates: {pin_coords}")

                        # Try other position attributes
                        for attr in ['pos', 'position', 'xy']:
                            if hasattr(pin, attr):
                                attr_val = getattr(pin, attr)
                                print(f"  {attr}: {attr_val}")

                # Try accessing different symbol representations
                if hasattr(tas5830_symbol, '__getitem__'):
                    try:
                        for i in range(min(len(tas5830_symbol), 2)):
                            symbol_unit = tas5830_symbol[i]
                            print(f"\nSymbol unit {i}: {symbol_unit}")
                            if hasattr(symbol_unit, 'pin'):
                                print(f"  Has pins: {len(list(symbol_unit.pin))}")
                    except Exception as e:
                        print(f"  Error accessing symbol units: {e}")

            else:
                print("❌ TAS5830 symbol not found in library")

                # Show available symbols
                print(f"\nAvailable symbols:")
                for i, symbol in enumerate(schem.lib_symbols):
                    if i >= 10:
                        print("  ... (truncated)")
                        break
                    try:
                        symbol_name = str(symbol).split("'")[1] if "'" in str(symbol) else str(symbol)
                        print(f"  {symbol_name}")
                    except:
                        pass

        else:
            print("❌ No lib_symbols found in schematic")

        # Alternative: calculate positions geometrically
        print(f"\n🔧 Geometric Pin Estimation for TAS5830")
        tas5830_center = tas5830.at.value[:2] if hasattr(tas5830.at, 'value') else [float(tas5830.at[0]), float(tas5830.at[1])]

        def estimate_tas5830_pin_position(pin_number, component_center):
            """Estimate TAS5830 pin positions based on HTSSOP-32 package."""
            center_x, center_y = component_center
            pin_num = int(pin_number)

            # TAS5830 is HTSSOP-32 package: 32 pins, 8 pins per side
            # Pin 1 starts bottom-left, goes counter-clockwise
            package_width = 7.0  # mm
            package_height = 7.0  # mm
            pin_spacing = 0.65  # mm

            if pin_num <= 8:
                # Bottom side (pins 1-8)
                x = center_x - (package_width/2) + (pin_num - 1) * pin_spacing
                y = center_y - (package_height/2) - 1.0  # Pin extension
            elif pin_num <= 16:
                # Right side (pins 9-16)
                x = center_x + (package_width/2) + 1.0  # Pin extension
                y = center_y - (package_height/2) + (pin_num - 9) * pin_spacing
            elif pin_num <= 24:
                # Top side (pins 17-24)
                x = center_x + (package_width/2) - (pin_num - 17) * pin_spacing
                y = center_y + (package_height/2) + 1.0  # Pin extension
            else:
                # Left side (pins 25-32)
                x = center_x - (package_width/2) - 1.0  # Pin extension
                y = center_y + (package_height/2) - (pin_num - 25) * pin_spacing

            return [x, y]

        # Test estimation on problematic pins
        test_pins = [8, 10, 25, 26]
        print(f"TAS5830 center: {tas5830_center}")
        print(f"Estimated pin positions:")
        for pin_num in test_pins:
            estimated_pos = estimate_tas5830_pin_position(pin_num, tas5830_center)
            print(f"  Pin {pin_num}: {estimated_pos}")

    except Exception as e:
        print(f"❌ Symbol lookup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    lookup_tas5830_symbol_pins()