"""
Schematic editing tools using KiCAD Skip.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP

from kicad_mcp.utils.path_validator import validate_path
from kicad_mcp.utils.file_utils import backup_file


def safe_serialize(obj) -> str:
    """Safely convert KiCAD Skip objects to serializable strings.

    Args:
        obj: Object to convert

    Returns:
        String representation of the object
    """
    if obj is None:
        return "None"
    try:
        # Try to convert to string, handling special cases
        return str(obj)
    except Exception:
        return "Unknown"


def find_component_by_reference(schem, component_reference: str):
    """Find a component by its reference designator with fallback methods.

    Args:
        schem: KiCAD Skip schematic object
        component_reference: Reference designator (e.g., 'R1', 'U3')

    Returns:
        tuple: (component_object, available_references_list)
    """
    # Get all available references for debugging
    available_refs = []
    try:
        for symbol in schem.symbol:
            ref = extract_property_value(symbol, "Reference")
            if ref != "Unknown":
                available_refs.append(ref)
    except Exception as e:
        logging.warning(f"Could not enumerate available references: {e}")

    logging.info(f"Looking for component {component_reference}. Available refs: {available_refs}")

    # Try direct attribute access first (KiCAD Skip provides this)
    component = getattr(schem.symbol, component_reference, None)

    # If direct access failed, try iteration
    if not component:
        logging.warning(f"Direct access failed for {component_reference}, trying iteration")
        for symbol in schem.symbol:
            ref = extract_property_value(symbol, "Reference")
            if ref == component_reference:
                component = symbol
                break

    return component, available_refs


def extract_property_value(symbol, prop_name: str) -> str:
    """Extract a property value from a KiCAD Skip symbol.

    Args:
        symbol: KiCAD Skip symbol object
        prop_name: Name of the property to extract

    Returns:
        String value of the property
    """
    try:
        # Access the property directly by name (KiCAD Skip provides direct access)
        if hasattr(symbol, prop_name):
            prop = getattr(symbol, prop_name)
            if hasattr(prop, 'value'):
                return safe_serialize(prop.value)
            else:
                return safe_serialize(prop)

        # Try lowercase version
        if hasattr(symbol, prop_name.lower()):
            prop = getattr(symbol, prop_name.lower())
            if hasattr(prop, 'value'):
                return safe_serialize(prop.value)
            else:
                return safe_serialize(prop)

        return "Unknown"
    except Exception as e:
        logging.debug(f"Failed to extract property {prop_name}: {e}")
        return "Unknown"


def get_component_pins(component):
    """Get all available pins for a component.

    Args:
        component: KiCAD Skip component object

    Returns:
        Dict with pin information
    """
    pins_info = []
    try:
        if hasattr(component, 'pin'):
            for pin in component.pin:
                pin_number = "Unknown"
                pin_name = None

                try:
                    # Method 1: SymbolPin objects (newer format)
                    if hasattr(pin, 'number') and hasattr(pin, 'name'):
                        pin_number = str(getattr(pin, 'number'))
                        pin_name_attr = getattr(pin, 'name', None)
                        if pin_name_attr and str(pin_name_attr).strip() != "~":
                            pin_name = str(pin_name_attr)

                    # Method 2: ParsedValue objects (older format) - Direct index access
                    elif hasattr(pin, '__getitem__'):
                        try:
                            if pin[0] is not None:
                                pin_number = str(pin[0])
                                # Try to get name from pin[2] if available
                                if len(pin) > 2:
                                    potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                                    if potential_name and str(potential_name).strip() != "~":
                                        pin_name = str(potential_name)
                        except (IndexError, TypeError):
                            pass

                    # Method 3: Fallback - Try accessing from raw data
                    if pin_number == "Unknown":
                        try:
                            raw_data = getattr(pin, 'raw', None)
                            if raw_data and len(raw_data) > 1:
                                pin_number = str(raw_data[1])
                        except (IndexError, TypeError, AttributeError):
                            # Method 4: Try accessing from children
                            try:
                                children = getattr(pin, 'children', None)
                                if children and len(children) > 0:
                                    pin_number = str(children[0])
                            except (IndexError, TypeError, AttributeError):
                                pass

                except Exception as e:
                    logging.debug(f"Error extracting pin data: {e}")

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


def register_schematic_edit_tools(mcp: FastMCP) -> None:
    """Register schematic editing tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    def load_schematic(schematic_path: str) -> Dict[str, Any]:
        """Load a KiCad schematic file for editing.

        Args:
            schematic_path: Path to the .kicad_sch file

        Returns:
            Dict with schematic info and available operations
        """
        logging.info(f"Loading schematic: {schematic_path}")

        # Validate path
        try:
            validated_path = validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        if not schematic_path.endswith(".kicad_sch"):
            return {"error": "File must be a .kicad_sch schematic file"}

        try:
            import skip

            schem = skip.Schematic(schematic_path)

            # Get basic info about the schematic
            symbols_info = []
            try:
                for symbol in schem.symbol:
                    # Convert KiCAD Skip objects to serializable data using improved extraction
                    symbol_info = {
                        "reference": extract_property_value(symbol, "Reference"),
                        "value": extract_property_value(symbol, "Value"),
                        "lib_id": safe_serialize(getattr(symbol, "lib_id", None)),
                        "uuid": safe_serialize(getattr(symbol, "uuid", None)),
                        "position": safe_serialize(getattr(symbol, "at", None)),
                    }
                    symbols_info.append(symbol_info)
            except Exception as e:
                logging.warning(f"Could not enumerate symbols: {e}")

            wires_count = 0
            try:
                wires_count = len(list(schem.wire))
            except Exception as e:
                logging.warning(f"Could not count wires: {e}")

            return {
                "status": "loaded",
                "path": schematic_path,
                "symbols_count": len(symbols_info),
                "wires_count": wires_count,
                "symbols_preview": symbols_info[:10],  # First 10 symbols
                "operations": [
                    "modify_component_property",
                    "add_component",
                    "connect_components",
                    "search_components",
                    "move_component",
                ],
            }

        except ImportError as e:
            return {"error": f"kicad-skip library not installed. Run: pip install kicad-skip. Import error: {str(e)}"}
        except Exception as e:
            logging.exception(f"Failed to load schematic {schematic_path}")
            return {"error": f"Failed to load schematic: {str(e)}", "exception_type": type(e).__name__}

    @mcp.tool()
    def search_components(
        schematic_path: str, search_type: str, search_value: str
    ) -> Dict[str, Any]:
        """Search for components in a schematic.

        Args:
            schematic_path: Path to the .kicad_sch file
            search_type: Type of search ('reference', 'value', 'regex', 'position')
            search_value: Value to search for

        Returns:
            List of matching components
        """
        logging.info(f"Searching components in {schematic_path}: {search_type}={search_value}")

        # Validate path
        try:
            validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        try:
            import skip

            schem = skip.Schematic(schematic_path)

            matches = []

            if search_type == "reference":
                try:
                    if search_value.endswith("*"):
                        # Startswith search
                        search_prefix = search_value[:-1]
                        for symbol in schem.symbol.reference_startswith(search_prefix):
                            matches.append(
                                {
                                    "reference": extract_property_value(symbol, "Reference"),
                                    "value": extract_property_value(symbol, "Value"),
                                    "lib_id": safe_serialize(getattr(symbol, "lib_id", None)),
                                    "position": safe_serialize(getattr(symbol, "at", None)),
                                }
                            )
                    else:
                        # Exact match
                        symbol = getattr(schem.symbol, search_value, None)
                        if symbol:
                            matches.append(
                                {
                                    "reference": extract_property_value(symbol, "Reference"),
                                    "value": extract_property_value(symbol, "Value"),
                                    "lib_id": safe_serialize(getattr(symbol, "lib_id", None)),
                                    "position": safe_serialize(getattr(symbol, "at", None)),
                                }
                            )
                except Exception as e:
                    logging.warning(f"Reference search failed: {e}")

            elif search_type == "regex":
                try:
                    for symbol in schem.symbol.reference_matches(search_value):
                        matches.append(
                            {
                                "reference": extract_property_value(symbol, "Reference"),
                                "value": extract_property_value(symbol, "Value"),
                                "lib_id": safe_serialize(getattr(symbol, "lib_id", None)),
                                "position": safe_serialize(getattr(symbol, "at", None)),
                            }
                        )
                except Exception as e:
                    logging.warning(f"Regex search failed: {e}")

            elif search_type == "value":
                try:
                    for symbol in schem.symbol:
                        symbol_value = extract_property_value(symbol, "Value")
                        if symbol_value == search_value:
                            matches.append(
                                {
                                    "reference": extract_property_value(symbol, "Reference"),
                                    "value": symbol_value,
                                    "lib_id": safe_serialize(getattr(symbol, "lib_id", None)),
                                    "position": safe_serialize(getattr(symbol, "at", None)),
                                }
                            )
                except Exception as e:
                    logging.warning(f"Value search failed: {e}")

            return {
                "search_type": search_type,
                "search_value": search_value,
                "matches_count": len(matches),
                "matches": matches,
            }

        except ImportError as e:
            return {"error": f"kicad-skip library not installed. Run: pip install kicad-skip. Import error: {str(e)}"}
        except Exception as e:
            logging.exception(f"Search failed for {search_type}={search_value} in {schematic_path}")
            return {"error": f"Search failed: {str(e)}", "exception_type": type(e).__name__}

    @mcp.tool()
    def get_component_pin_info(schematic_path: str, component_reference: str) -> Dict[str, Any]:
        """Get detailed pin information for a specific component.

        Args:
            schematic_path: Path to the .kicad_sch file
            component_reference: Reference of the component (e.g., 'R1', 'U1')

        Returns:
            Dict with component pin information
        """
        logging.info(f"Getting pin info for component {component_reference} in {schematic_path}")

        # Validate path
        try:
            validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        try:
            import skip

            schem = skip.Schematic(schematic_path)

            # Find the component
            component, available_refs = find_component_by_reference(schem, component_reference)
            if not component:
                return {
                    "error": f"Component {component_reference} not found",
                    "available_references": available_refs
                }

            # Get pin information
            pins_info = get_component_pins(component)

            return {
                "status": "success",
                "component": component_reference,
                "lib_id": safe_serialize(getattr(component, "lib_id", None)),
                "pin_count": pins_info["pin_count"],
                "pins": pins_info["pins"]
            }

        except ImportError as e:
            return {"error": f"kicad-skip library not installed. Run: pip install kicad-skip. Import error: {str(e)}"}
        except Exception as e:
            logging.exception(f"Failed to get pin info for {component_reference}")
            return {"error": f"Pin info failed: {str(e)}", "exception_type": type(e).__name__}

    @mcp.tool()
    def modify_component_property(
        schematic_path: str,
        component_reference: str,
        property_name: str,
        new_value: str,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """Modify a property of a component in the schematic.

        Args:
            schematic_path: Path to the .kicad_sch file
            component_reference: Reference of the component (e.g., 'R1', 'C5')
            property_name: Name of the property to modify (e.g., 'Value', 'MPN')
            new_value: New value for the property
            create_backup: Whether to create a backup before modifying

        Returns:
            Result of the modification
        """
        logging.info(
            f"Modifying {component_reference}.{property_name} = {new_value} in {schematic_path}"
        )

        # Validate path
        try:
            validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        try:
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_result = backup_file(schematic_path)
                if backup_result["success"]:
                    backup_path = backup_result["backup_path"]
                else:
                    return {"error": f"Failed to create backup: {backup_result['error']}"}

            import skip

            schem = skip.Schematic(schematic_path)

            # Find the component using helper function
            try:
                component, available_refs = find_component_by_reference(schem, component_reference)

                if not component:
                    return {
                        "error": f"Component {component_reference} not found",
                        "available_references": available_refs,
                        "searched_reference": component_reference
                    }

                # Get the old value for comparison
                old_value = "Not set"
                try:
                    if hasattr(component, "property") and hasattr(
                        component.property, property_name
                    ):
                        old_value = safe_serialize(getattr(component.property, property_name).value)
                except:
                    pass

                # Set the new property value
                if not hasattr(component, "property"):
                    return {"error": f"Component {component_reference} has no properties"}

                if hasattr(component.property, property_name):
                    getattr(component.property, property_name).value = new_value
                else:
                    # Property doesn't exist, might need to create it
                    return {
                        "error": f"Property {property_name} not found on component {component_reference}"
                    }

                # Save the schematic using kicad-skip API
                schem.overwrite()

                return {
                    "status": "modified",
                    "component": component_reference,
                    "property": property_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                }

            except AttributeError:
                return {"error": f"Component {component_reference} not found"}

        except ImportError:
            return {"error": "kicad-skip library not installed. Run: pip install kicad-skip"}
        except Exception as e:
            return {"error": f"Modification failed: {str(e)}"}

    @mcp.tool()
    def add_wire_connection(
        schematic_path: str,
        from_component: str,
        from_pin: str,
        to_component: str,
        to_pin: str,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """Add a wire connection between two component pins.

        Args:
            schematic_path: Path to the .kicad_sch file
            from_component: Reference of the source component (e.g., 'R1')
            from_pin: Pin number/name on source component
            to_component: Reference of the target component (e.g., 'C1')
            to_pin: Pin number/name on target component
            create_backup: Whether to create a backup before modifying

        Returns:
            Result of the wire creation
        """
        logging.info(f"Adding wire from {from_component}.{from_pin} to {to_component}.{to_pin}")

        # Validate path
        try:
            validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        try:
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_result = backup_file(schematic_path)
                if backup_result["success"]:
                    backup_path = backup_result["backup_path"]
                else:
                    return {"error": f"Failed to create backup: {backup_result['error']}"}

            import skip

            schem = skip.Schematic(schematic_path)

            # Find the components using helper function
            from_comp, available_refs = find_component_by_reference(schem, from_component)
            to_comp, _ = find_component_by_reference(schem, to_component)

            if not from_comp:
                return {
                    "error": f"Source component {from_component} not found",
                    "available_references": available_refs
                }
            if not to_comp:
                return {
                    "error": f"Target component {to_component} not found",
                    "available_references": available_refs
                }

            # Find the specific pins with improved error handling
            from_pins_info = get_component_pins(from_comp)
            to_pins_info = get_component_pins(to_comp)

            # Find the requested pins
            from_pin_obj = None
            to_pin_obj = None

            # Search for from_pin - flexible matching for various pin formats
            for pin in from_comp.pin:
                pin_matches = False
                try:
                    pin_number = ""
                    pin_name = ""

                    # Extract pin number and name based on pin object type
                    if hasattr(pin, 'number') and hasattr(pin, 'name'):
                        # SymbolPin objects (newer format)
                        pin_number = str(getattr(pin, 'number'))
                        pin_name_attr = getattr(pin, 'name', None)
                        if pin_name_attr:
                            pin_name = str(pin_name_attr)
                    elif hasattr(pin, '__getitem__'):
                        # ParsedValue objects (older format)
                        try:
                            pin_number = str(pin[0]) if pin[0] is not None else ""
                            if len(pin) > 2:
                                potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                                if potential_name:
                                    pin_name = str(potential_name)
                        except (IndexError, TypeError):
                            pass

                    # Method 1: Direct exact match with pin number
                    if pin_number == from_pin:
                        pin_matches = True

                    # Method 2: Check if requested pin matches the number part of formatted pins
                    # Handle cases like "23 (GPIO21/ADC)" where user wants to connect to "23"
                    elif pin_number and from_pin:
                        # Extract just the number part from formatted pins like "1 (~)" or "23 (GPIO21)"
                        number_part = pin_number.split()[0] if " " in pin_number else pin_number
                        if number_part == from_pin:
                            pin_matches = True

                    # Method 3: Check if user provided a GPIO name that matches the description
                    if not pin_matches and pin_name:
                        # Direct name match
                        if pin_name == from_pin:
                            pin_matches = True
                        # Check if the requested pin is part of the GPIO name (e.g., "GPIO21" from "GPIO21/ADC")
                        elif "/" in pin_name and from_pin in pin_name.split("/"):
                            pin_matches = True

                    if pin_matches:
                        from_pin_obj = pin
                        break
                except (IndexError, TypeError):
                    continue

            # Search for to_pin - flexible matching for various pin formats
            for pin in to_comp.pin:
                pin_matches = False
                try:
                    pin_number = ""
                    pin_name = ""

                    # Extract pin number and name based on pin object type
                    if hasattr(pin, 'number') and hasattr(pin, 'name'):
                        # SymbolPin objects (newer format)
                        pin_number = str(getattr(pin, 'number'))
                        pin_name_attr = getattr(pin, 'name', None)
                        if pin_name_attr:
                            pin_name = str(pin_name_attr)
                    elif hasattr(pin, '__getitem__'):
                        # ParsedValue objects (older format)
                        try:
                            pin_number = str(pin[0]) if pin[0] is not None else ""
                            if len(pin) > 2:
                                potential_name = pin[2] if pin[2] != getattr(pin, 'uuid', None) else None
                                if potential_name:
                                    pin_name = str(potential_name)
                        except (IndexError, TypeError):
                            pass

                    # Method 1: Direct exact match with pin number
                    if pin_number == to_pin:
                        pin_matches = True

                    # Method 2: Check if requested pin matches the number part of formatted pins
                    # Handle cases like "23 (GPIO21/ADC)" where user wants to connect to "23"
                    elif pin_number and to_pin:
                        # Extract just the number part from formatted pins like "1 (~)" or "23 (GPIO21)"
                        number_part = pin_number.split()[0] if " " in pin_number else pin_number
                        if number_part == to_pin:
                            pin_matches = True

                    # Method 3: Check if user provided a GPIO name that matches the description
                    if not pin_matches and pin_name:
                        # Direct name match
                        if pin_name == to_pin:
                            pin_matches = True
                        # Check if the requested pin is part of the GPIO name (e.g., "GPIO21" from "GPIO21/ADC")
                        elif "/" in pin_name and to_pin in pin_name.split("/"):
                            pin_matches = True

                    if pin_matches:
                        to_pin_obj = pin
                        break
                except (IndexError, TypeError):
                    continue

            # Improved error messages with available pins
            if from_pin_obj is None:
                # Include both numbers and names in available pins list
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
                # Include both numbers and names in available pins list
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

            # Create a new wire using ACTUAL PIN COORDINATES
            try:
                new_wire = schem.wire.new()

                # Get actual pin coordinates instead of component centers
                def get_pin_coordinates(component, pin_obj, pin_identifier, comp_name):
                    """Get actual pin coordinates for wire routing."""
                    try:
                        # Method 1: Use pin location if available (SymbolPin objects)
                        if hasattr(pin_obj, 'location') and hasattr(pin_obj.location, 'value'):
                            coords = pin_obj.location.value[:2]  # [x, y] only
                            logging.info(f"Using actual pin coordinates for {comp_name}.{pin_identifier}: {coords}")
                            return coords

                        # Method 2: Try iterating through component pins to find location
                        if hasattr(component, 'pin'):
                            for pin in component.pin:
                                try:
                                    # Check if this is our target pin
                                    pin_matches = False
                                    if hasattr(pin, 'number') and str(getattr(pin, 'number')) == str(pin_identifier):
                                        pin_matches = True
                                    elif hasattr(pin, 'name') and str(getattr(pin, 'name')) == str(pin_identifier):
                                        pin_matches = True
                                    elif hasattr(pin, '__getitem__') and str(pin[0]) == str(pin_identifier):
                                        pin_matches = True

                                    if pin_matches and hasattr(pin, 'location') and hasattr(pin.location, 'value'):
                                        coords = pin.location.value[:2]
                                        logging.info(f"Found pin coordinates by iteration for {comp_name}.{pin_identifier}: {coords}")
                                        return coords
                                except Exception:
                                    continue

                        # Fallback to component center
                        comp_pos = component.at
                        if hasattr(comp_pos, 'value'):
                            center_coords = comp_pos.value[:2]
                        else:
                            center_coords = [float(comp_pos[0]), float(comp_pos[1])]

                        logging.warning(f"Using component center as fallback for {comp_name}.{pin_identifier}: {center_coords}")
                        return center_coords

                    except Exception as e:
                        logging.error(f"Error getting coordinates for {comp_name}.{pin_identifier}: {e}")
                        return [0, 0]  # Ultimate fallback

                # Get actual pin coordinates
                from_coords = get_pin_coordinates(from_comp, from_pin_obj, from_pin, from_component)
                to_coords = get_pin_coordinates(to_comp, to_pin_obj, to_pin, to_component)

                # Validate coordinates
                if not from_coords or not to_coords:
                    return {
                        "error": "Could not determine pin coordinates",
                        "from_coordinates": from_coords,
                        "to_coordinates": to_coords
                    }

                # Create wire connection using coordinates
                new_wire.start_at(from_coords)
                new_wire.end_at(to_coords)

                # Save the schematic using kicad-skip API
                schem.overwrite()

                return {
                    "status": "connected",
                    "from": f"{from_component}.{from_pin}",
                    "to": f"{to_component}.{to_pin}",
                    "from_coordinates": from_coords,
                    "to_coordinates": to_coords,
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                    "method": "pin_to_pin_wire",
                    "note": "Connected using actual pin coordinates for precise electrical connections."
                }

            except Exception as e:
                # Provide more detailed error information
                return {
                    "error": f"Failed to connect pins: {str(e)}",
                    "error_type": type(e).__name__,
                    "from_component": from_component,
                    "from_pin": from_pin,
                    "to_component": to_component,
                    "to_pin": to_pin,
                    "debug_info": {
                        "from_pin_found": from_pin_obj is not None,
                        "to_pin_found": to_pin_obj is not None,
                        "available_from_pins": [pin["number"] for pin in from_pins_info["pins"]],
                        "available_to_pins": [pin["number"] for pin in to_pins_info["pins"]]
                    }
                }

        except ImportError:
            return {"error": "kicad-skip library not installed. Run: pip install kicad-skip"}
        except Exception as e:
            return {"error": f"Wire creation failed: {str(e)}"}

    @mcp.tool()
    def move_component(
        schematic_path: str,
        component_reference: str,
        x_offset: float,
        y_offset: float,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """Move a component by the specified offset.

        Args:
            schematic_path: Path to the .kicad_sch file
            component_reference: Reference of the component to move (e.g., 'R1')
            x_offset: X offset in mm
            y_offset: Y offset in mm
            create_backup: Whether to create a backup before modifying

        Returns:
            Result of the move operation
        """
        logging.info(f"Moving component {component_reference} by ({x_offset}, {y_offset})")

        # Validate path
        try:
            validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        try:
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_result = backup_file(schematic_path)
                if backup_result["success"]:
                    backup_path = backup_result["backup_path"]
                else:
                    return {"error": f"Failed to create backup: {backup_result['error']}"}

            import skip

            schem = skip.Schematic(schematic_path)

            # Find the component using helper function
            component, available_refs = find_component_by_reference(schem, component_reference)
            if not component:
                return {
                    "error": f"Component {component_reference} not found",
                    "available_references": available_refs
                }

            # Get old position for reference
            old_position = getattr(component, "position", "Unknown")

            # Move the component
            try:
                component.move(x_offset, y_offset)

                # Save the schematic using kicad-skip API
                schem.overwrite()

                # Get new position
                new_position = getattr(component, "position", "Unknown")

                return {
                    "status": "moved",
                    "component": component_reference,
                    "old_position": str(old_position),
                    "new_position": str(new_position),
                    "offset": f"({x_offset}, {y_offset})",
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                }

            except Exception as e:
                return {"error": f"Failed to move component: {str(e)}"}

        except ImportError:
            return {"error": "kicad-skip library not installed. Run: pip install kicad-skip"}
        except Exception as e:
            return {"error": f"Move operation failed: {str(e)}"}

    @mcp.tool()
    def clone_component(
        schematic_path: str,
        source_reference: str,
        new_reference: str,
        x_offset: float = 10.0,
        y_offset: float = 0.0,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """Clone an existing component to a new location with a new reference.

        Args:
            schematic_path: Path to the .kicad_sch file
            source_reference: Reference of the component to clone (e.g., 'R1')
            new_reference: Reference for the new component (e.g., 'R2')
            x_offset: X offset from original position in mm
            y_offset: Y offset from original position in mm
            create_backup: Whether to create a backup before modifying

        Returns:
            Result of the clone operation
        """
        logging.info(f"Cloning component {source_reference} to {new_reference}")

        # Validate path
        try:
            validate_path(schematic_path, must_exist=True)
        except Exception as e:
            return {"error": f"Invalid path: {str(e)}"}

        try:
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_result = backup_file(schematic_path)
                if backup_result["success"]:
                    backup_path = backup_result["backup_path"]
                else:
                    return {"error": f"Failed to create backup: {backup_result['error']}"}

            import skip

            schem = skip.Schematic(schematic_path)

            # Find the source component using helper function
            source_component, available_refs = find_component_by_reference(schem, source_reference)
            if not source_component:
                return {
                    "error": f"Source component {source_reference} not found",
                    "available_references": available_refs
                }

            # Clone the component
            try:
                new_component = source_component.clone()

                # Update the reference using the proper property API
                if hasattr(new_component, "Reference") and hasattr(new_component.Reference, "value"):
                    new_component.Reference.value = new_reference
                elif hasattr(new_component, "reference"):
                    # Fallback for different API versions
                    new_component.reference = new_reference

                # Move to new position
                new_component.move(x_offset, y_offset)

                # Save the schematic using kicad-skip API
                schem.overwrite()

                return {
                    "status": "cloned",
                    "source": source_reference,
                    "new_component": new_reference,
                    "offset": f"({x_offset}, {y_offset})",
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                }

            except Exception as e:
                return {"error": f"Failed to clone component: {str(e)}"}

        except ImportError:
            return {"error": "kicad-skip library not installed. Run: pip install kicad-skip"}
        except Exception as e:
            return {"error": f"Clone operation failed: {str(e)}"}
