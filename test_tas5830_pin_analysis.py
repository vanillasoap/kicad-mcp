#!/usr/bin/env python3
"""
Analyze why TAS5830 pins all have the same coordinates
"""

import skip

def analyze_tas5830_pins():
    """Deep dive into TAS5830 pin structure to understand coordinate issue."""
    print("🔍 TAS5830 Pin Analysis - Finding Coordinate Issue")
    print("=" * 60)

    try:
        production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
        schem = skip.Schematic(production_path)

        # Compare ESP32 vs TAS5830 pin structures
        esp32 = getattr(schem.symbol, "U3", None)
        tas5830 = getattr(schem.symbol, "U1", None)

        if not esp32 or not tas5830:
            print("❌ Components not found")
            return

        print(f"--- ESP32 (U3) vs TAS5830 (U1) Comparison ---")

        # Component centers
        esp32_center = esp32.at.value if hasattr(esp32.at, 'value') else [float(esp32.at[0]), float(esp32.at[1])]
        tas5830_center = tas5830.at.value if hasattr(tas5830.at, 'value') else [float(tas5830.at[0]), float(tas5830.at[1])]

        print(f"ESP32 center: {esp32_center}")
        print(f"TAS5830 center: {tas5830_center}")

        # Analyze pin structures
        print(f"\n--- ESP32 Pin Structure Analysis ---")
        if hasattr(esp32, 'pin'):
            pin_count = 0
            for i, pin in enumerate(esp32.pin):
                pin_count += 1
                if i >= 3:  # Only analyze first 3 pins
                    break
                print(f"\nESP32 Pin {i+1}:")
                print(f"  Type: {type(pin)}")
                print(f"  Has number: {hasattr(pin, 'number')}")
                print(f"  Has location: {hasattr(pin, 'location')}")

                if hasattr(pin, 'number'):
                    print(f"  Number: {getattr(pin, 'number')}")
                if hasattr(pin, 'location'):
                    location = pin.location
                    print(f"  Location object: {location}")
                    if hasattr(location, 'value'):
                        coords = location.value
                        print(f"  ✅ Coordinates: {coords}")

        print(f"\n--- TAS5830 Pin Structure Analysis ---")
        if hasattr(tas5830, 'pin'):
            tas_pin_count = 0
            for i, pin in enumerate(tas5830.pin):
                tas_pin_count += 1
                if i >= 5:  # Only analyze first 5 pins
                    break
                print(f"\nTAS5830 Pin {i+1}:")
                print(f"  Type: {type(pin)}")
                print(f"  Has number: {hasattr(pin, 'number')}")
                print(f"  Has location: {hasattr(pin, 'location')}")

                if hasattr(pin, 'number'):
                    print(f"  Number: {getattr(pin, 'number')}")
                if hasattr(pin, 'name'):
                    print(f"  Name: {getattr(pin, 'name')}")
                if hasattr(pin, 'location'):
                    location = pin.location
                    print(f"  Location object: {location}")
                    if hasattr(location, 'value'):
                        coords = location.value
                        print(f"  ✅ Coordinates: {coords}")
                    else:
                        print(f"  ❌ Location has no .value attribute")
                else:
                    print(f"  ❌ Pin has no .location attribute")

                # Check all attributes
                attrs = [attr for attr in dir(pin) if not attr.startswith('_')]
                print(f"  Available attributes: {attrs}")

                # If it's a ParsedValue, check its structure
                if hasattr(pin, '__getitem__'):
                    try:
                        print(f"  ParsedValue length: {len(pin)}")
                        for j in range(min(len(pin), 5)):
                            element = pin[j]
                            print(f"  [{j}]: {element} (type: {type(element)})")
                    except:
                        pass

        # Test our coordinate extraction function on both
        print(f"\n--- Testing Coordinate Extraction ---")

        def debug_get_pin_coordinates(component, pin_identifier, comp_name):
            """Debug version of pin coordinate extraction."""
            print(f"\n🔧 Extracting coordinates for {comp_name}.{pin_identifier}")

            try:
                comp_pos = component.at
                comp_center = comp_pos.value[:2] if hasattr(comp_pos, 'value') else [float(comp_pos[0]), float(comp_pos[1])]
                print(f"  Component center: {comp_center}")

                # Method 1: Direct pin object access (if we have it)
                found_pin = None
                if hasattr(component, 'pin'):
                    for pin in component.pin:
                        try:
                            if hasattr(pin, 'number') and str(getattr(pin, 'number')) == str(pin_identifier):
                                found_pin = pin
                                print(f"  ✅ Found pin by number match")
                                break
                            elif hasattr(pin, '__getitem__') and str(pin[0]) == str(pin_identifier):
                                found_pin = pin
                                print(f"  ✅ Found pin by index access")
                                break
                        except Exception as e:
                            continue

                if found_pin:
                    print(f"  Pin object: {found_pin}")
                    print(f"  Pin type: {type(found_pin)}")

                    if hasattr(found_pin, 'location'):
                        location = found_pin.location
                        print(f"  Location object: {location}")
                        if hasattr(location, 'value'):
                            coords = location.value[:2]
                            print(f"  ✅ Pin coordinates: {coords}")
                            return coords
                        else:
                            print(f"  ❌ Location object has no .value")
                    else:
                        print(f"  ❌ Pin has no .location attribute")

                print(f"  ⚠️ Falling back to component center: {comp_center}")
                return comp_center

            except Exception as e:
                print(f"  ❌ Error: {e}")
                return [0, 0]

        # Test specific pins
        print("\n=== ESP32 Pin Tests ===")
        debug_get_pin_coordinates(esp32, '23', 'U3')
        debug_get_pin_coordinates(esp32, '16', 'U3')

        print("\n=== TAS5830 Pin Tests ===")
        debug_get_pin_coordinates(tas5830, '8', 'U1')
        debug_get_pin_coordinates(tas5830, '10', 'U1')
        debug_get_pin_coordinates(tas5830, '25', 'U1')

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_tas5830_pins()