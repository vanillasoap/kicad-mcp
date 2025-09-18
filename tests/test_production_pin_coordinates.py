#!/usr/bin/env python3
"""
Test pin coordinate access methods with production schematic
"""

import skip

def test_production_pin_coordinates():
    """Test accessing actual pin coordinates in production schematic."""
    print("🎯 Testing Pin Coordinate Access - Production Schematic")
    print("=" * 60)

    production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"

    try:
        schem = skip.Schematic(production_path)
        print("✅ Production schematic loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load production schematic: {e}")
        return

    # Test ESP32 component (U3)
    try:
        esp32 = getattr(schem.symbol, "U3", None)
        if not esp32:
            print("❌ ESP32 component (U3) not found")
            return

        print(f"\n--- ESP32 (U3) Pin Coordinate Analysis ---")

        # Get component position
        comp_pos = esp32.at
        print(f"Component position object: {comp_pos}")
        print(f"Component position type: {type(comp_pos)}")

        # Try to get position values
        try:
            if hasattr(comp_pos, 'value'):
                pos_values = comp_pos.value
                print(f"Position values: {pos_values}")
            else:
                # Try direct access
                pos_values = [float(comp_pos[0]), float(comp_pos[1])]
                rotation = float(comp_pos[2]) if len(comp_pos) > 2 else 0
                print(f"Position: x={pos_values[0]}, y={pos_values[1]}, rotation={rotation}")
        except Exception as e:
            print(f"⚠️ Could not extract position values: {e}")

        # Test pin access methods
        print(f"\n🔍 Testing Pin Access Methods:")

        # Method 1: Check if pins have location attribute
        if hasattr(esp32, 'pin') and len(esp32.pin) > 0:
            test_pins = ['23', 'CHIP_PU', '16']  # Test different pin types

            for pin_id in test_pins:
                print(f"\n--- Testing Pin '{pin_id}' ---")

                # Try by name access
                try:
                    if hasattr(esp32.pin, pin_id):
                        pin = getattr(esp32.pin, pin_id)
                        print(f"✅ Pin access by name: {pin}")

                        if hasattr(pin, 'location'):
                            location = pin.location
                            print(f"✅ Pin location object: {location}")
                            if hasattr(location, 'value'):
                                coords = location.value
                                print(f"✅ Pin coordinates: {coords}")
                            else:
                                print(f"⚠️ Location has no .value attribute")
                        else:
                            print(f"⚠️ Pin has no .location attribute")
                    else:
                        print(f"❌ Pin '{pin_id}' not accessible by name")
                except Exception as e:
                    print(f"❌ Error accessing pin by name: {e}")

                # Try by iteration to find pin
                try:
                    found_pin = False
                    for i, pin in enumerate(esp32.pin):
                        try:
                            # Check if this matches our target pin
                            if hasattr(pin, 'number') and str(getattr(pin, 'number')) == pin_id:
                                found_pin = True
                                print(f"✅ Found pin by iteration at index {i}")

                                # Test coordinate access
                                if hasattr(pin, 'location'):
                                    location = pin.location
                                    print(f"✅ Pin location: {location}")
                                    if hasattr(location, 'value'):
                                        coords = location.value
                                        print(f"✅ Actual coordinates: {coords}")
                                        # Calculate offset from component center
                                        try:
                                            offset_x = coords[0] - pos_values[0]
                                            offset_y = coords[1] - pos_values[1]
                                            print(f"📐 Pin offset: dx={offset_x:.2f}mm, dy={offset_y:.2f}mm")
                                        except:
                                            pass
                                break

                            elif hasattr(pin, 'name') and str(getattr(pin, 'name')) == pin_id:
                                found_pin = True
                                print(f"✅ Found pin by name match at index {i}")
                                break
                        except Exception as pin_e:
                            continue

                    if not found_pin:
                        print(f"⚠️ Pin '{pin_id}' not found by iteration")

                except Exception as e:
                    print(f"❌ Error during pin iteration: {e}")

        # Test getting all pin names/numbers for reference
        print(f"\n📋 Available Pin Information:")
        try:
            pin_names = []
            if hasattr(esp32, 'pin'):
                for i, pin in enumerate(esp32.pin[:5]):  # First 5 pins
                    try:
                        if hasattr(pin, 'number') and hasattr(pin, 'name'):
                            pin_num = getattr(pin, 'number')
                            pin_name = getattr(pin, 'name')
                            pin_info = f"{pin_num}"
                            if pin_name and str(pin_name).strip() != "~":
                                pin_info += f" ({pin_name})"
                            pin_names.append(pin_info)
                        elif hasattr(pin, '__getitem__'):
                            pin_num = str(pin[0]) if pin[0] is not None else "Unknown"
                            pin_names.append(pin_num)
                    except:
                        pin_names.append(f"Pin{i}")

            print(f"Sample pins: {pin_names}")
        except Exception as e:
            print(f"⚠️ Could not enumerate pins: {e}")

    except Exception as e:
        print(f"❌ Error testing ESP32: {e}")
        import traceback
        traceback.print_exc()

def test_pin_coordinate_extraction():
    """Test the actual pin coordinate extraction function."""
    print(f"\n🔧 Testing Pin Coordinate Extraction Function")
    print("=" * 50)

    def get_pin_coordinates(component, pin_identifier):
        """Get actual pin coordinates for wire routing."""
        try:
            comp_pos = component.at
            # Extract component position
            if hasattr(comp_pos, 'value'):
                comp_center = comp_pos.value[:2]
            else:
                comp_center = [float(comp_pos[0]), float(comp_pos[1])]

            print(f"Component center: {comp_center}")

            # Method 1: Try accessing by name
            if hasattr(component.pin, pin_identifier):
                pin = getattr(component.pin, pin_identifier)
                if hasattr(pin, 'location') and hasattr(pin.location, 'value'):
                    coords = pin.location.value[:2]
                    print(f"✅ Pin coordinates by name: {coords}")
                    return coords

            # Method 2: Try iterating through pins
            if hasattr(component, 'pin'):
                for pin in component.pin:
                    try:
                        # Check number match
                        if hasattr(pin, 'number') and str(getattr(pin, 'number')) == str(pin_identifier):
                            if hasattr(pin, 'location') and hasattr(pin.location, 'value'):
                                coords = pin.location.value[:2]
                                print(f"✅ Pin coordinates by number: {coords}")
                                return coords

                        # Check name match
                        if hasattr(pin, 'name') and str(getattr(pin, 'name')) == str(pin_identifier):
                            if hasattr(pin, 'location') and hasattr(pin.location, 'value'):
                                coords = pin.location.value[:2]
                                print(f"✅ Pin coordinates by name match: {coords}")
                                return coords

                    except Exception as pin_e:
                        continue

            # Fallback to component center
            print(f"⚠️ Using component center as fallback")
            return comp_center

        except Exception as e:
            print(f"❌ Error in coordinate extraction: {e}")
            # Ultimate fallback
            return [0, 0]

    # Test with production schematic
    try:
        production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
        schem = skip.Schematic(production_path)
        esp32 = getattr(schem.symbol, "U3", None)

        if esp32:
            # Test specific pins
            test_pins = ['23', 'CHIP_PU', '16']
            for pin_id in test_pins:
                print(f"\n--- Extracting coordinates for pin '{pin_id}' ---")
                coords = get_pin_coordinates(esp32, pin_id)
                print(f"Final coordinates: {coords}")

    except Exception as e:
        print(f"❌ Error in coordinate extraction test: {e}")

if __name__ == "__main__":
    test_production_pin_coordinates()
    test_pin_coordinate_extraction()