#!/usr/bin/env python3
"""
Test the updated wire routing with actual pin coordinates
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'kicad_mcp', 'tools'))

from schematic_edit_tools import SchematicEditTools

def test_actual_pin_routing():
    """Test wire connections using actual pin coordinates."""
    print("🔌 Testing Actual Pin Coordinate Wire Routing")
    print("=" * 60)

    # Test with production schematic
    production_path = "/Users/so/Library/CloudStorage/Dropbox/Kicad/TAS5830_ESP32P4_Audio_Amp/TAS5830_ESP32P4_Audio_Amp.kicad_sch"

    tools = SchematicEditTools()

    # Test cases that should now work with actual pin coordinates
    test_connections = [
        ("U3", "23", "U1", "10", "ESP32 GPIO21 to TAS5830 pin 10"),
        ("U3", "CHIP_PU", "R_PU", "1", "ESP32 CHIP_PU to pull-up resistor"),
        ("U3", "16", "U1", "25", "ESP32 GPIO15 to TAS5830 pin 25"),
    ]

    for i, (from_comp, from_pin, to_comp, to_pin, description) in enumerate(test_connections):
        print(f"\n--- Test {i+1}: {description} ---")
        print(f"Connection: {from_comp}.{from_pin} → {to_comp}.{to_pin}")

        result = tools.add_wire_connection(
            schematic_path=production_path,
            from_component=from_comp,
            from_pin=from_pin,
            to_component=to_comp,
            to_pin=to_pin,
            create_backup=True
        )

        if result.get('status') == 'connected':
            print(f"✅ SUCCESS!")
            print(f"  Method: {result.get('method')}")
            print(f"  From: {result['from_coordinates']}")
            print(f"  To: {result['to_coordinates']}")
            print(f"  Note: {result.get('note')}")

            # Calculate distance to show it's not component-to-component
            from_x, from_y = result['from_coordinates']
            to_x, to_y = result['to_coordinates']
            distance = ((to_x - from_x)**2 + (to_y - from_y)**2)**0.5
            print(f"  Wire length: {distance:.2f}mm")

        else:
            print(f"❌ FAILED")
            print(f"  Error: {result.get('error')}")
            if 'available_pins' in result:
                print(f"  Available pins: {result['available_pins'][:5]}...")

    print(f"\n🎯 Expected Results:")
    print("✅ Pin coordinates should be different from component centers")
    print("✅ Method should show 'pin_to_pin_wire' instead of 'coordinate_based_wire'")
    print("✅ ESP32 pin 23 should connect to actual pin location, not component center")
    print("✅ Wire routing should be electrically meaningful")

if __name__ == "__main__":
    test_actual_pin_routing()