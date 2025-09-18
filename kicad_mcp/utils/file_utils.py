"""
File handling utilities for KiCad MCP Server.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any

from kicad_mcp.utils.kicad_utils import get_project_name_from_path


def get_project_files(project_path: str) -> dict[str, str]:
    """Get all files related to a KiCad project.

    Args:
        project_path: Path to the .kicad_pro file

    Returns:
        Dictionary mapping file types to file paths
    """
    from kicad_mcp.config import DATA_EXTENSIONS, KICAD_EXTENSIONS

    project_dir = os.path.dirname(project_path)
    project_name = get_project_name_from_path(project_path)

    files = {}

    # Check for standard KiCad files
    for file_type, extension in KICAD_EXTENSIONS.items():
        if file_type == "project":
            # We already have the project file
            files[file_type] = project_path
            continue

        file_path = os.path.join(project_dir, f"{project_name}{extension}")
        if os.path.exists(file_path):
            files[file_type] = file_path

    # Check for data files
    try:
        for ext in DATA_EXTENSIONS:
            for file in os.listdir(project_dir):
                if file.startswith(project_name) and file.endswith(ext):
                    # Extract the type from filename (e.g., project_name-bom.csv -> bom)
                    file_type = file[len(project_name) :].strip("-_")
                    file_type = file_type.split(".")[0]
                    if not file_type:
                        file_type = ext[1:]  # Use extension if no specific type

                    files[file_type] = os.path.join(project_dir, file)
    except (OSError, FileNotFoundError):
        # Directory doesn't exist or can't be accessed - return what we have
        pass

    return files


def load_project_json(project_path: str) -> dict[str, Any] | None:
    """Load and parse a KiCad project file.

    Args:
        project_path: Path to the .kicad_pro file

    Returns:
        Parsed JSON data or None if parsing failed
    """
    try:
        with open(project_path) as f:
            return json.load(f)
    except Exception:
        return None


def backup_file(file_path: str, backup_dir: str = None) -> dict[str, Any]:
    """Create a backup of a file before modifying it.

    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backups (default: same directory as file)

    Returns:
        Dict with success status and backup path or error message
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File does not exist: {file_path}"}

    try:
        # Determine backup directory
        if backup_dir is None:
            backup_dir = os.path.dirname(file_path)

        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        file_name = os.path.basename(file_path)
        name_parts = os.path.splitext(file_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name_parts[0]}_backup_{timestamp}{name_parts[1]}"
        backup_path = os.path.join(backup_dir, backup_name)

        # Create the backup
        shutil.copy2(file_path, backup_path)

        return {
            "success": True,
            "backup_path": backup_path,
            "original_path": file_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create backup: {str(e)}"
        }
