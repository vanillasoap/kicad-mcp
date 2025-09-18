#!/usr/bin/env python3
"""
Debug why TAS5830 geometric estimation isn't working
"""

import skip

def debug_tas5830_coordinate_logic():
    """Debug the actual pin coordinate extraction logic for TAS5830."""
    print("🐛 Debugging TAS5830 Coordinate Extraction Logic")
    print("=" * 60)

    try:
        production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
        schem = skip.Schematic(production_path)

        tas5830 = getattr(schem.symbol, "U1", None)
        if not tas5830:
            print("❌ TAS5830 not found")
            return

        print(f"✅ TAS5830 component found")
        print(f"Component type: {type(tas5830)}")
        print(f"Component position: {tas5830.at}")

        # Get center coordinates the same way the MCP does
        comp_pos = tas5830.at
        if hasattr(comp_pos, 'value'):
            center_coords = comp_pos.value[:2]
        else:
            center_coords = [float(comp_pos[0]), float(comp_pos[1])]

        print(f"Center coordinates: {center_coords}")

        # Test the exact logic from the MCP wire connection function
        print(f"\n🔍 Testing MCP Pin Extraction Logic:")

        test_pins = ['1', '8', '10', '32']
        for pin_id in test_pins:
            print(f"\n--- Testing Pin {pin_id} ---")

            # Simulate the MCP's get_pin_coordinates function logic
            found_pin = None
            pin_matches = False

            # Method 1: Try accessing by name (shouldn't work for TAS5830)
            if hasattr(tas5830.pin, pin_id):
                pin = getattr(tas5830.pin, pin_id)
                print(f"  ✅ Found pin by name access: {pin}")
                found_pin = pin
            else:
                print(f"  ❌ Pin '{pin_id}' not accessible by name")

            # Method 2: Try iterating through component pins to find location
            if not found_pin and hasattr(tas5830, 'pin'):
                for pin in tas5830.pin:
                    try:
                        # Check if this is our target pin (MCP logic)
                        if hasattr(pin, 'number') and str(getattr(pin, 'number')) == str(pin_id):
                            print(f"  ✅ Found pin by number match: {pin}")
                            found_pin = pin
                            pin_matches = True
                            break
                        elif hasattr(pin, 'name') and str(getattr(pin, 'name')) == str(pin_id):
                            print(f"  ✅ Found pin by name match: {pin}")
                            found_pin = pin
                            pin_matches = True
                            break
                        elif hasattr(pin, '__getitem__') and str(pin[0]) == str(pin_id):
                            print(f"  ✅ Found pin by index access: {pin}")
                            found_pin = pin
                            pin_matches = True
                            break
                    except Exception as e:
                        continue

            # Now check what the MCP would do with this pin
            if found_pin:
                print(f"  Pin object type: {type(found_pin)}")
                print(f"  Has location: {hasattr(found_pin, 'location')}")

                if hasattr(found_pin, 'location'):
                    location = found_pin.location
                    print(f"  Location object: {location}")
                    print(f"  Location type: {type(location)}")
                    print(f"  Has location.value: {hasattr(location, 'value')}")

                    if hasattr(location, 'value'):
                        coords = location.value[:2]
                        print(f"  📍 FOUND COORDINATES: {coords}")
                        print(f"  ⚠️  This explains why geometric estimation isn't called!")

                        # Check if these are meaningful coordinates or just component center
                        if coords == center_coords:
                            print(f"  🚨 PROBLEM: Pin coordinates same as component center!")
                        else:
                            print(f"  ✅ Pin coordinates different from center")
                    else:
                        print(f"  ❌ Location has no .value attribute")
                else:
                    print(f"  ❌ Pin has no .location attribute - would use geometric estimation")

                    # Test geometric estimation
                    print(f"  🔧 Testing geometric estimation:")
                    estimated = estimate_geometric_coordinates(pin_id, center_coords)
                    print(f"  Estimated coordinates: {estimated}")

            else:
                print(f"  ❌ Pin not found by any method")

        # Check if TAS5830 pins actually have location data that matches component center
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        print("If TAS5830 pins have .location attributes that return component center,")
        print("then the MCP never reaches the geometric estimation fallback!")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

def estimate_geometric_coordinates(pin_identifier, center_coords):
    """Test version of geometric estimation."""
    try:
        pin_num = int(pin_identifier)
        center_x, center_y = center_coords

        # TAS5830 - HTSSOP-32 package estimation
        package_width = 6.5
        package_height = 6.5
        pin_spacing = 0.65
        pin_extension = 1.2

        if pin_num <= 8:
            # Bottom side (pins 1-8), left to right
            x = center_x - (package_width/2) + (pin_num - 1) * pin_spacing
            y = center_y - (package_height/2) - pin_extension
        elif pin_num <= 16:
            # Right side (pins 9-16), bottom to top
            x = center_x + (package_width/2) + pin_extension
            y = center_y - (package_height/2) + (pin_num - 9) * pin_spacing
        elif pin_num <= 24:
            # Top side (pins 17-24), right to left
            x = center_x + (package_width/2) - (pin_num - 17) * pin_spacing
            y = center_y + (package_height/2) + pin_extension
        else:
            # Left side (pins 25-32), top to bottom
            x = center_x - (package_width/2) - pin_extension
            y = center_y + (package_height/2) - (pin_num - 25) * pin_spacing

        return [round(x, 2), round(y, 2)]
    except:
        return center_coords

if __name__ == "__main__":
    debug_tas5830_coordinate_logic()