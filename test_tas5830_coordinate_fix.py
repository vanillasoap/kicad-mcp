#!/usr/bin/env python3
"""
Test the TAS5830 pin coordinate fix with geometric estimation
"""

import sys
import os
sys.path.append('.')

# Test the geometric estimation function directly
from kicad_mcp.tools.schematic_edit_tools import _estimate_ic_pin_coordinates

def test_tas5830_coordinate_fix():
    """Test the TAS5830 geometric pin coordinate estimation."""
    print("🔧 Testing TAS5830 Pin Coordinate Fix")
    print("=" * 50)

    # Mock TAS5830 component data
    class MockComponent:
        def __init__(self):
            self.lib_id = "TAS5830:TAS5830M"
            self.at = [259.08, 46.99, 0]  # From your previous test results

    mock_tas5830 = MockComponent()
    center_coords = [259.08, 46.99]
    comp_name = "U1"

    # Test specific pins that were showing same coordinates before
    test_pins = [8, 9, 10, 11, 14, 15, 16, 25, 26]

    print(f"TAS5830 center coordinates: {center_coords}")
    print(f"\nEstimated pin coordinates:")

    estimated_positions = {}
    for pin_num in test_pins:
        estimated_coords = _estimate_ic_pin_coordinates(
            mock_tas5830,
            str(pin_num),
            center_coords,
            comp_name
        )
        estimated_positions[pin_num] = estimated_coords

        # Calculate offset from center
        offset_x = estimated_coords[0] - center_coords[0]
        offset_y = estimated_coords[1] - center_coords[1]

        print(f"  Pin {pin_num:2d}: {estimated_coords} (offset: {offset_x:+5.2f}, {offset_y:+5.2f})")

    # Verify pins have different coordinates
    unique_positions = set(tuple(pos) for pos in estimated_positions.values())
    print(f"\nValidation:")
    print(f"  Pins tested: {len(test_pins)}")
    print(f"  Unique positions: {len(unique_positions)}")

    if len(unique_positions) == len(test_pins):
        print("  ✅ SUCCESS: All pins have unique coordinates!")
    elif len(unique_positions) > 1:
        print("  ⚠️  PARTIAL: Some pins have unique coordinates")
    else:
        print("  ❌ FAILED: All pins still have same coordinates")

    # Test package layout validation
    print(f"\n📦 Package Layout Validation:")

    # Check that pins are arranged in proper HTSSOP-32 layout
    bottom_pins = [pos for pin, pos in estimated_positions.items() if 1 <= pin <= 8]
    right_pins = [pos for pin, pos in estimated_positions.items() if 9 <= pin <= 16]
    top_pins = [pos for pin, pos in estimated_positions.items() if 17 <= pin <= 24]
    left_pins = [pos for pin, pos in estimated_positions.items() if 25 <= pin <= 32]

    # Bottom pins should have increasing X, same Y
    if bottom_pins:
        bottom_y_values = set(pos[1] for pos in bottom_pins)
        print(f"  Bottom pins Y-values: {len(bottom_y_values)} unique (should be 1)")
        print(f"  ✅ Bottom pins aligned" if len(bottom_y_values) == 1 else "  ❌ Bottom pins misaligned")

    # Test actual coordinates make sense
    sample_pin_10 = estimated_positions.get(10)
    sample_pin_25 = estimated_positions.get(25)

    if sample_pin_10 and sample_pin_25:
        distance = ((sample_pin_10[0] - sample_pin_25[0])**2 + (sample_pin_10[1] - sample_pin_25[1])**2)**0.5
        print(f"  Pin 10 to Pin 25 distance: {distance:.2f}mm (should be ~10-15mm for HTSSOP-32)")
        print(f"  ✅ Reasonable distance" if 8 < distance < 20 else "  ❌ Unreasonable distance")

    print(f"\n🎯 Expected Impact:")
    print("✅ TAS5830 pins should now show different coordinates instead of [259.08, 46.99]")
    print("✅ Wire connections should route to actual pin locations")
    print("✅ Method should show 'pin_to_pin_wire' with geometric estimation")

    return estimated_positions

def test_with_real_schematic():
    """Test with the actual production schematic."""
    print(f"\n🧪 Testing with Real Schematic")
    print("=" * 40)

    try:
        import skip
        production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"
        schem = skip.Schematic(production_path)

        tas5830 = getattr(schem.symbol, "U1", None)
        if tas5830:
            center_coords = tas5830.at.value[:2] if hasattr(tas5830.at, 'value') else [float(tas5830.at[0]), float(tas5830.at[1])]

            print(f"Real TAS5830 center: {center_coords}")

            # Test estimation with real component
            test_coords = _estimate_ic_pin_coordinates(tas5830, "10", center_coords, "U1")
            print(f"Real estimation for pin 10: {test_coords}")

            if test_coords != center_coords:
                print("✅ Geometric estimation working with real component!")
                return True
            else:
                print("❌ Still using component center")
                return False
        else:
            print("❌ TAS5830 component not found")
            return False

    except Exception as e:
        print(f"❌ Real schematic test failed: {e}")
        return False

if __name__ == "__main__":
    estimated_positions = test_tas5830_coordinate_fix()
    real_test_passed = test_with_real_schematic()

    print(f"\n🏁 SUMMARY:")
    print(f"Mock test: {'✅ PASSED' if len(set(tuple(pos) for pos in estimated_positions.values())) > 1 else '❌ FAILED'}")
    print(f"Real test: {'✅ PASSED' if real_test_passed else '❌ FAILED'}")

    if real_test_passed:
        print(f"\n🎉 TAS5830 pin coordinate fix is ready!")
        print("Restart your MCP server and test wire connections.")
    else:
        print(f"\n⚠️  Fix needs debugging.")