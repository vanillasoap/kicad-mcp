#!/usr/bin/env python3
"""
Test the formatted pin matching logic with simulated complex pins
"""

import skip

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

class MockPin:
    """Mock pin object to simulate complex pin structures."""

    def __init__(self, number, name=None, uuid_val="test-uuid"):
        self.data = [number]
        if name:
            self.data.append("uuid")  # Skip uuid placeholder
            self.data.append(name)
        self.uuid_val = uuid_val

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    @property
    def uuid(self):
        return self.uuid_val

def test_formatted_pin_matching():
    """Test the new flexible pin matching logic with formatted pins."""
    print("🧪 Testing Formatted Pin Matching Logic")
    print("=" * 50)

    # Simulate different pin scenarios
    test_cases = [
        # (pin_object, user_requests, expected_results)
        (
            MockPin("23", "GPIO21/ADC"),
            ["23", "GPIO21/ADC", "GPIO21", "ADC"],
            "ESP32 pin with GPIO name"
        ),
        (
            MockPin("1", "~"),
            ["1"],
            "Resistor pin with tilde"
        ),
        (
            MockPin("12", "SDA/I2C"),
            ["12", "SDA", "I2C", "SDA/I2C"],
            "Multi-function GPIO pin"
        ),
        (
            MockPin("5"),
            ["5"],
            "Simple numbered pin"
        ),
    ]

    for pin_obj, user_requests, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"Pin object: {pin_obj.data}")

        for requested_pin in user_requests:
            result = test_pin_matching_logic(pin_obj, requested_pin)
            status = "✅" if result else "❌"
            print(f"  '{requested_pin}' -> {status} {result}")

def test_pin_matching_logic(pin_obj, requested_pin):
    """Test the flexible pin matching logic (simulates the fixed wire connection logic)."""
    try:
        # Get the raw pin number from the pin object
        pin_number = str(pin_obj[0]) if pin_obj[0] is not None else ""

        # Method 1: Direct exact match with pin number
        if pin_number == requested_pin:
            return "Direct match"

        # Method 2: Check if requested pin matches the number part of formatted pins
        # Handle cases like "23 (GPIO21/ADC)" where user wants to connect to "23"
        elif pin_number and requested_pin:
            # Extract just the number part from formatted pins like "1 (~)" or "23 (GPIO21)"
            number_part = pin_number.split()[0] if " " in pin_number else pin_number
            if number_part == requested_pin:
                return "Number part match"

        # Method 3: Check if user provided a GPIO name that matches the description
        if len(pin_obj) > 2:
            potential_name = pin_obj[2] if pin_obj[2] != pin_obj.uuid else None
            if potential_name:
                name_str = str(potential_name)
                # Direct name match
                if name_str == requested_pin:
                    return "Name match"
                # Check if the requested pin is part of the GPIO name (e.g., "GPIO21" from "GPIO21/ADC")
                elif "/" in name_str and requested_pin in name_str.split("/"):
                    return "GPIO name part match"

        return False

    except Exception as e:
        return f"Error: {e}"

def test_real_wire_connection_simulation():
    """Test a full wire connection simulation with the improved matching."""
    print(f"\n🔌 Wire Connection Simulation")
    print("=" * 40)

    # Load real schematic
    schem = skip.Schematic('test_wiring.kicad_sch')

    # Test cases that should work with improved matching
    test_connections = [
        ("R_SCL", "1", "U1", "1", "Basic resistor to IC"),
        ("R_SCL", "2", "U1", "2", "Basic resistor to IC"),
    ]

    for from_comp, from_pin, to_comp, to_pin, description in test_connections:
        print(f"\n--- {description}: {from_comp}.{from_pin} → {to_comp}.{to_pin} ---")

        try:
            # Get components
            from_component = getattr(schem.symbol, from_comp, None)
            to_component = getattr(schem.symbol, to_comp, None)

            if not from_component or not to_component:
                print("❌ Components not found")
                continue

            # Test pin matching with improved logic
            from_pin_found = find_pin_with_flexible_matching(from_component, from_pin)
            to_pin_found = find_pin_with_flexible_matching(to_component, to_pin)

            from_status = "✅" if from_pin_found else "❌"
            to_status = "✅" if to_pin_found else "❌"

            print(f"  {from_comp}.{from_pin}: {from_status}")
            print(f"  {to_comp}.{to_pin}: {to_status}")

            if from_pin_found and to_pin_found:
                print(f"  🎉 Connection would succeed with improved matching!")
            else:
                print(f"  ⚠️  Connection would fail")

        except Exception as e:
            print(f"❌ Error: {e}")

def find_pin_with_flexible_matching(component, requested_pin):
    """Find pin using the improved flexible matching logic."""
    if not hasattr(component, 'pin'):
        return False

    for pin in component.pin:
        try:
            # Get the raw pin number from the pin object
            pin_number = str(pin[0]) if pin[0] is not None else ""

            # Method 1: Direct exact match
            if pin_number == requested_pin:
                return True

            # Method 2: Number part matching
            elif pin_number and requested_pin:
                number_part = pin_number.split()[0] if " " in pin_number else pin_number
                if number_part == requested_pin:
                    return True

            # Method 3: Name matching
            if len(pin) > 2:
                potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                if potential_name:
                    name_str = str(potential_name)
                    if name_str == requested_pin:
                        return True
                    elif "/" in name_str and requested_pin in name_str.split("/"):
                        return True

        except (IndexError, TypeError):
            continue

    return False

if __name__ == "__main__":
    test_formatted_pin_matching()
    test_real_wire_connection_simulation()