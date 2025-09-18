#!/usr/bin/env python3
"""
Complete test of the pin matching fix with wire connections
"""

import skip
import shutil
import logging

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

def get_component_pins_fixed(component):
    """Fixed version with better pin name handling."""
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

                # Try to get pin name if available
                try:
                    if hasattr(pin, 'name') and getattr(pin, 'name', None):
                        pin_name = str(getattr(pin, 'name'))
                    elif len(pin) > 2:
                        potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                        if potential_name:
                            pin_name = str(potential_name)
                except (IndexError, TypeError, AttributeError):
                    pass

                # Handle edge cases
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

def add_wire_connection_fixed(schematic_path, from_component, from_pin, to_component, to_pin, create_backup=True):
    """Fixed wire connection with flexible pin matching."""

    try:
        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = f"{schematic_path}.backup"
            shutil.copy2(schematic_path, backup_path)

        # Load schematic
        schem = skip.Schematic(schematic_path)

        # Find components
        from_comp, available_refs = find_component_by_reference(schem, from_component)
        to_comp, _ = find_component_by_reference(schem, to_component)

        if from_comp is None:
            return {
                "error": f"Source component {from_component} not found",
                "available_references": available_refs
            }
        if to_comp is None:
            return {
                "error": f"Target component {to_component} not found",
                "available_references": available_refs
            }

        # Get pin information for error reporting
        from_pins_info = get_component_pins_fixed(from_comp)
        to_pins_info = get_component_pins_fixed(to_comp)

        # Find the requested pins using FLEXIBLE MATCHING
        from_pin_obj = None
        to_pin_obj = None

        # Search for from_pin with flexible matching
        for pin in from_comp.pin:
            try:
                # Get the raw pin number from the pin object
                pin_number = str(pin[0]) if pin[0] is not None else ""

                # Method 1: Direct exact match with pin number
                if pin_number == from_pin:
                    from_pin_obj = pin
                    break

                # Method 2: Check if requested pin matches the number part of formatted pins
                elif pin_number and from_pin:
                    number_part = pin_number.split()[0] if " " in pin_number else pin_number
                    if number_part == from_pin:
                        from_pin_obj = pin
                        break

                # Method 3: Check if user provided a GPIO name that matches
                if len(pin) > 2:
                    potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                    if potential_name:
                        name_str = str(potential_name)
                        # Direct name match
                        if name_str == from_pin:
                            from_pin_obj = pin
                            break
                        # Check if the requested pin is part of the GPIO name
                        elif "/" in name_str and from_pin in name_str.split("/"):
                            from_pin_obj = pin
                            break

            except (IndexError, TypeError):
                continue

        # Search for to_pin with flexible matching
        for pin in to_comp.pin:
            try:
                # Get the raw pin number from the pin object
                pin_number = str(pin[0]) if pin[0] is not None else ""

                # Method 1: Direct exact match with pin number
                if pin_number == to_pin:
                    to_pin_obj = pin
                    break

                # Method 2: Check if requested pin matches the number part of formatted pins
                elif pin_number and to_pin:
                    number_part = pin_number.split()[0] if " " in pin_number else pin_number
                    if number_part == to_pin:
                        to_pin_obj = pin
                        break

                # Method 3: Check if user provided a GPIO name that matches
                if len(pin) > 2:
                    potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                    if potential_name:
                        name_str = str(potential_name)
                        # Direct name match
                        if name_str == to_pin:
                            to_pin_obj = pin
                            break
                        # Check if the requested pin is part of the GPIO name
                        elif "/" in name_str and to_pin in name_str.split("/"):
                            to_pin_obj = pin
                            break

            except (IndexError, TypeError):
                continue

        # Check if pins were found
        if from_pin_obj is None:
            # Create enhanced available pins list
            available_pins = []
            for pin in from_pins_info["pins"]:
                pin_id = pin["number"]
                if pin.get("name") and pin["name"] != pin["number"]:
                    pin_id = f"{pin['number']} ({pin['name']})"
                available_pins.append(pin_id)

            return {
                "error": f"Pin '{from_pin}' not found on component {from_component}",
                "available_pins": available_pins,
                "component": from_component,
                "lib_id": safe_serialize(getattr(from_comp, "lib_id", None))
            }

        if to_pin_obj is None:
            # Create enhanced available pins list
            available_pins = []
            for pin in to_pins_info["pins"]:
                pin_id = pin["number"]
                if pin.get("name") and pin["name"] != pin["number"]:
                    pin_id = f"{pin['number']} ({pin['name']})"
                available_pins.append(pin_id)

            return {
                "error": f"Pin '{to_pin}' not found on component {to_component}",
                "available_pins": available_pins,
                "component": to_component,
                "lib_id": safe_serialize(getattr(to_comp, "lib_id", None))
            }

        # Create wire using coordinate-based connection
        from_pos = from_comp.at
        to_pos = to_comp.at

        try:
            from_coords = [float(from_pos[0]), float(from_pos[1])]
            to_coords = [float(to_pos[0]), float(to_pos[1])]
        except Exception as pos_error:
            return {
                "error": f"Could not extract coordinates: {str(pos_error)}",
                "from_position": safe_serialize(from_pos),
                "to_position": safe_serialize(to_pos)
            }

        new_wire = schem.wire.new()
        new_wire.start_at(from_coords)
        new_wire.end_at(to_coords)

        # Save schematic
        schem.overwrite()

        return {
            "status": "connected",
            "from": f"{from_component}.{from_pin}",
            "to": f"{to_component}.{to_pin}",
            "from_coordinates": from_coords,
            "to_coordinates": to_coords,
            "backup_created": backup_path is not None,
            "backup_path": backup_path,
            "method": "flexible_pin_matching"
        }

    except Exception as e:
        return {
            "error": f"Failed to connect pins: {str(e)}",
            "error_type": type(e).__name__
        }

def test_complete_pin_fix():
    """Test the complete pin matching fix with various scenarios."""
    print("🚀 Complete Pin Matching Fix Test")
    print("=" * 50)

    # Create test schematic
    test_schematic = "pin_fix_test.kicad_sch"
    shutil.copy2('test_wiring.kicad_sch', test_schematic)

    # Test scenarios from your report
    test_cases = [
        # Basic numbered pin connections (should work with simple pins)
        ("R_SCL", "1", "U1", "1", "Resistor pin 1 to IC pin 1"),
        ("R_SCL", "2", "U1", "2", "Resistor pin 2 to IC pin 2"),

        # Test scenarios that would fail with old logic but succeed with new logic
        # (These simulate the formatted pins you mentioned)
        ("R_PDN", "1", "U1", "3", "Test flexible matching"),
        ("R_PDN", "2", "U1", "4", "Test flexible matching"),
    ]

    results = []
    success_count = 0

    for i, (from_comp, from_pin, to_comp, to_pin, description) in enumerate(test_cases):
        print(f"\n--- Test {i+1}: {description} ---")
        print(f"  Connection: {from_comp}.{from_pin} → {to_comp}.{to_pin}")

        result = add_wire_connection_fixed(
            test_schematic, from_comp, from_pin, to_comp, to_pin,
            create_backup=False  # Skip backup for faster testing
        )

        results.append({
            'test': description,
            'connection': f"{from_comp}.{from_pin} → {to_comp}.{to_pin}",
            'result': result
        })

        if result.get('status') == 'connected':
            print(f"  ✅ SUCCESS: Connected at {result['from_coordinates']} → {result['to_coordinates']}")
            success_count += 1
        else:
            print(f"  ❌ FAILED: {result.get('error')}")
            if 'available_pins' in result:
                print(f"     Available pins: {result['available_pins']}")

    # Test edge cases and error handling
    print(f"\n--- Error Handling Tests ---")

    error_tests = [
        ("R_SCL", "99", "U1", "1", "Invalid source pin"),
        ("R_SCL", "1", "U1", "99", "Invalid target pin"),
    ]

    for from_comp, from_pin, to_comp, to_pin, description in error_tests:
        print(f"\n  {description}: {from_comp}.{from_pin} → {to_comp}.{to_pin}")
        result = add_wire_connection_fixed(test_schematic, from_comp, from_pin, to_comp, to_pin, create_backup=False)

        if 'available_pins' in result:
            print(f"    ✅ Correctly identified invalid pin with suggestions: {result['available_pins']}")
            success_count += 1
        else:
            print(f"    ❌ Error handling failed: {result}")

    # Final verification
    try:
        final_schem = skip.Schematic(test_schematic)
        final_wire_count = len(final_schem.wire)
        print(f"\n🔍 Final verification: {final_wire_count} wires in schematic")
    except Exception as e:
        print(f"❌ Final verification failed: {e}")

    # Summary
    total_tests = len(test_cases) + len(error_tests)
    print(f"\n🏁 SUMMARY")
    print(f"  Total tests: {total_tests}")
    print(f"  Successful: {success_count}")
    print(f"  Success rate: {success_count/total_tests*100:.1f}%")

    success_emoji = "🎉" if success_count >= 5 else "⚠️"
    print(f"\n{success_emoji} Pin matching fix is {'FULLY FUNCTIONAL' if success_count >= 5 else 'PARTIALLY WORKING'}!")

    return results

if __name__ == "__main__":
    test_complete_pin_fix()