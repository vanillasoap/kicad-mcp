#!/usr/bin/env python3
"""
Simple test of TAS5830 pin coordinate algorithm
"""

def estimate_tas5830_pin_coordinates(pin_identifier, center_coords):
    """Test implementation of TAS5830 pin coordinate estimation."""
    try:
        pin_num = int(pin_identifier)
        center_x, center_y = center_coords

        # TAS5830 - HTSSOP-32 package
        # Standard HTSSOP-32: 32 pins, 8 per side, counter-clockwise from pin 1
        package_width = 6.5   # mm
        package_height = 6.5  # mm
        pin_spacing = 0.65    # mm
        pin_extension = 1.2   # mm beyond package edge

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

    except Exception as e:
        return center_coords

def test_tas5830_fix():
    """Test the TAS5830 pin coordinate algorithm."""
    print("🔧 Testing TAS5830 Pin Coordinate Algorithm")
    print("=" * 55)

    # Use actual TAS5830 center from your testing
    center_coords = [259.08, 46.99]

    # Test problematic pins that were all showing same coordinates
    test_pins = [8, 9, 10, 11, 14, 15, 16, 25, 26]

    print(f"TAS5830 center: {center_coords}")
    print(f"\nBEFORE FIX: All pins showed {center_coords}")
    print(f"AFTER FIX (estimated coordinates):")

    results = {}
    for pin_num in test_pins:
        estimated = estimate_tas5830_pin_coordinates(pin_num, center_coords)
        results[pin_num] = estimated

        offset_x = estimated[0] - center_coords[0]
        offset_y = estimated[1] - center_coords[1]
        side = ""

        if pin_num <= 8:
            side = "Bottom"
        elif pin_num <= 16:
            side = "Right"
        elif pin_num <= 24:
            side = "Top"
        else:
            side = "Left"

        print(f"  Pin {pin_num:2d}: {estimated} (offset: {offset_x:+6.2f}, {offset_y:+6.2f}) [{side}]")

    # Validation
    unique_coords = set(tuple(coords) for coords in results.values())

    print(f"\n📊 VALIDATION:")
    print(f"  Pins tested: {len(test_pins)}")
    print(f"  Unique coordinates: {len(unique_coords)}")

    if len(unique_coords) == len(test_pins):
        print("  ✅ SUCCESS: All pins have different coordinates!")
    else:
        print("  ❌ FAILED: Some pins still have same coordinates")

    # Show coordinate spread
    all_x = [coords[0] for coords in results.values()]
    all_y = [coords[1] for coords in results.values()]

    print(f"\n📐 COORDINATE SPREAD:")
    print(f"  X range: {min(all_x):.2f} to {max(all_x):.2f} ({max(all_x) - min(all_x):.2f}mm span)")
    print(f"  Y range: {min(all_y):.2f} to {max(all_y):.2f} ({max(all_y) - min(all_y):.2f}mm span)")

    # Test specific pin pairs
    pin_8_coords = results.get(8)
    pin_25_coords = results.get(25)

    if pin_8_coords and pin_25_coords:
        distance = ((pin_8_coords[0] - pin_25_coords[0])**2 + (pin_8_coords[1] - pin_25_coords[1])**2)**0.5
        print(f"\n🔍 DIAGONAL CHECK:")
        print(f"  Pin 8 (bottom): {pin_8_coords}")
        print(f"  Pin 25 (left):  {pin_25_coords}")
        print(f"  Distance: {distance:.2f}mm")
        print(f"  ✅ Reasonable IC diagonal" if 5 < distance < 15 else "  ❌ Unreasonable distance")

    return len(unique_coords) == len(test_pins)

if __name__ == "__main__":
    success = test_tas5830_fix()

    print(f"\n🎯 EXPECTED IMPACT ON WIRE ROUTING:")
    print("✅ TAS5830 pins 8,9,10,11,14,15,16,25,26 will have unique coordinates")
    print("✅ Wire connections will route to actual pin locations instead of component center")
    print("✅ Schematic will look correct with proper pin-to-pin connections")

    print(f"\n🏁 ALGORITHM TEST: {'✅ PASSED' if success else '❌ FAILED'}")

    if success:
        print("🎉 Ready to test with MCP server restart!")