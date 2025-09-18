#!/usr/bin/env python3
"""
Test the improved pin discovery functionality
"""

import skip
import logging

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

def get_component_pins_improved(component):
    """Improved version of get_component_pins with better pin name handling."""
    pins_info = []
    try:
        if hasattr(component, 'pin'):
            for pin in component.pin:
                pin_number = "Unknown"
                pin_name = None

                try:
                    # Method 1: Direct index access (most common)
                    if pin[0] is not None:
                        pin_number = str(pin[0])
                except (IndexError, TypeError):
                    # Method 2: Try accessing from raw data
                    try:
                        raw_data = getattr(pin, 'raw', None)
                        if raw_data and len(raw_data) > 1:
                            pin_number = str(raw_data[1])
                    except (IndexError, TypeError, AttributeError):
                        # Method 3: Try accessing from children
                        try:
                            children = getattr(pin, 'children', None)
                            if children and len(children) > 0:
                                pin_number = str(children[0])
                        except (IndexError, TypeError, AttributeError):
                            pass

                # Try to get pin name if available (for named pins like ESP32 modules)
                try:
                    # Some pins might have names in addition to numbers
                    if hasattr(pin, 'name') and getattr(pin, 'name', None):
                        pin_name = str(getattr(pin, 'name'))
                    elif len(pin) > 2:  # Check if there's a name field
                        potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                        if potential_name:
                            pin_name = str(potential_name)
                except (IndexError, TypeError, AttributeError):
                    pass

                # Handle edge cases where pin number might be empty or whitespace
                if not pin_number or pin_number.strip() == "":
                    pin_number = "Unknown"

                pin_info = {
                    "number": pin_number.strip(),
                    "name": pin_name.strip() if pin_name else None,
                    "uuid": safe_serialize(getattr(pin, "uuid", None))
                }
                pins_info.append(pin_info)
    except Exception as e:
        logging.warning(f"Could not enumerate pins for component: {e}")

    return {
        "pin_count": len(pins_info),
        "pins": pins_info
    }

def find_component_by_reference(schem, component_reference: str):
    """Find component by reference."""
    component = getattr(schem.symbol, component_reference, None)
    available_refs = [attr for attr in dir(schem.symbol) if not attr.startswith('_')]
    return component, available_refs

def test_improved_pin_discovery():
    """Test the improved pin discovery function."""
    print("=== Testing Improved Pin Discovery Function ===\n")

    schem = skip.Schematic('test_wiring.kicad_sch')

    components_to_test = ['R_SCL', 'R_PDN', 'U1']

    for comp_name in components_to_test:
        print(f"Testing {comp_name}:")
        comp, available_refs = find_component_by_reference(schem, comp_name)

        if comp:
            pins_result = get_component_pins_improved(comp)
            print(f"  Pin count: {pins_result['pin_count']}")
            print(f"  Pins:")

            for pin in pins_result['pins']:
                uuid_short = pin['uuid'][:30] + '...' if len(pin['uuid']) > 30 else pin['uuid']
                if pin['name']:
                    print(f"    Pin '{pin['number']}' (name: '{pin['name']}') UUID: {uuid_short}")
                else:
                    print(f"    Pin '{pin['number']}' UUID: {uuid_short}")

            # Test wire connection capability
            if pins_result['pin_count'] >= 2:
                pin1 = pins_result['pins'][0]['number']
                pin2 = pins_result['pins'][1]['number']
                print(f"  Wire connection test: Can connect pin '{pin1}' and pin '{pin2}' ✅")
            else:
                print(f"  Wire connection test: Not enough pins")
        else:
            print(f"  Component not found. Available: {available_refs}")
        print()

    # Test a simulated component with "Unknown" pins to understand the issue
    print("=== Simulating 'Unknown' Pin Issue ===")
    r_comp, _ = find_component_by_reference(schem, 'R_SCL')
    if r_comp:
        print("Simulating what might cause 'Unknown' pins:")

        for i, pin in enumerate(r_comp.pin[:2]):
            print(f"Pin {i+1} detailed analysis:")

            # Test various failure scenarios
            try:
                pin_0 = pin[0]
                print(f"  pin[0] = '{pin_0}' ✅")

                # Test if pin_0 could be None, empty, or whitespace
                if pin_0 is None:
                    print(f"  >>> Would result in 'Unknown' (pin[0] is None)")
                elif str(pin_0).strip() == "":
                    print(f"  >>> Would result in 'Unknown' (pin[0] is empty/whitespace)")
                else:
                    print(f"  >>> Would result in '{pin_0}' ✅")

            except Exception as e:
                print(f"  pin[0] access failed: {e} >>> Would result in 'Unknown'")

def test_wire_connection_with_improved_pins():
    """Test wire connections using the improved pin discovery."""
    print("\n=== Testing Wire Connection with Improved Pin Discovery ===")

    schem = skip.Schematic('test_wiring.kicad_sch')

    # Test resistor to IC connection
    r_comp, _ = find_component_by_reference(schem, 'R_SCL')
    u1_comp, _ = find_component_by_reference(schem, 'U1')

    if r_comp and u1_comp:
        r_pins = get_component_pins_improved(r_comp)
        u1_pins = get_component_pins_improved(u1_comp)

        print(f"R_SCL pins: {[pin['number'] for pin in r_pins['pins']]}")
        print(f"U1 pins: {[pin['number'] for pin in u1_pins['pins'][:5]]}...")

        # Try to match pins (simulate the wire connection logic)
        target_r_pin = '1'
        target_u1_pin = '2'

        r_pin_found = any(pin['number'] == target_r_pin for pin in r_pins['pins'])
        u1_pin_found = any(pin['number'] == target_u1_pin for pin in u1_pins['pins'])

        print(f"Can find R_SCL pin '{target_r_pin}': {r_pin_found}")
        print(f"Can find U1 pin '{target_u1_pin}': {u1_pin_found}")

        if r_pin_found and u1_pin_found:
            print("✅ Wire connection would succeed with improved pin discovery!")
        else:
            print("❌ Wire connection would fail - pins not found")

if __name__ == "__main__":
    test_improved_pin_discovery()
    test_wire_connection_with_improved_pins()