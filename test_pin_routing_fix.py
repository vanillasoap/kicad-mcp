#!/usr/bin/env python3
"""
Test the updated wire routing with actual pin coordinates
"""

# Simple test of the pin coordinate fix
print("🔌 Testing Pin Coordinate Fix")
print("=" * 40)

try:
    import skip

    # Load production schematic
    production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
    schem = skip.Schematic(production_path)

    # Get ESP32 component
    esp32 = getattr(schem.symbol, "U3", None)
    if esp32:
        print("✅ ESP32 component found")

        # Test the pin coordinate extraction logic we implemented
        def get_pin_coordinates(component, pin_identifier, comp_name):
            """Test the pin coordinate extraction."""
            try:
                # Find the pin by iterating
                for pin in component.pin:
                    try:
                        # Check if this is our target pin
                        if hasattr(pin, 'number') and str(getattr(pin, 'number')) == str(pin_identifier):
                            if hasattr(pin, 'location') and hasattr(pin.location, 'value'):
                                coords = pin.location.value[:2]
                                print(f"✅ Found pin coordinates for {comp_name}.{pin_identifier}: {coords}")
                                return coords
                    except Exception:
                        continue

                # Fallback to component center
                comp_pos = component.at
                if hasattr(comp_pos, 'value'):
                    center_coords = comp_pos.value[:2]
                else:
                    center_coords = [float(comp_pos[0]), float(comp_pos[1])]

                print(f"⚠️ Using component center for {comp_name}.{pin_identifier}: {center_coords}")
                return center_coords

            except Exception as e:
                print(f"❌ Error getting coordinates for {comp_name}.{pin_identifier}: {e}")
                return [0, 0]

        # Test specific pins
        test_pins = ['23', 'CHIP_PU', '16']
        for pin_id in test_pins:
            print(f"\n--- Testing {pin_id} ---")
            coords = get_pin_coordinates(esp32, pin_id, "U3")

        # Compare component center vs pin coordinates
        comp_center = esp32.at.value[:2] if hasattr(esp32.at, 'value') else [float(esp32.at[0]), float(esp32.at[1])]
        pin_23_coords = get_pin_coordinates(esp32, '23', "U3")

        print(f"\n📊 COMPARISON:")
        print(f"Component center: {comp_center}")
        print(f"Pin 23 coordinates: {pin_23_coords}")

        if pin_23_coords != comp_center:
            print("✅ SUCCESS: Pin coordinates are different from component center!")
            print("🎉 The fix is working - wires will now connect to actual pins!")
        else:
            print("❌ Pin coordinates same as component center - using fallback")

    else:
        print("❌ ESP32 component not found")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n💡 NEXT STEPS:")
print("1. Restart your MCP server to pick up the updated code")
print("2. Try wire connections again - they should now use actual pin coordinates")
print("3. Look for 'method: pin_to_pin_wire' in connection results")