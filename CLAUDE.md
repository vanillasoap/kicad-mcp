# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Install dependencies:**
```bash
make install
```

**Run tests:**
```bash
make test
# Or run specific test file:
make test tests/test_specific.py
```

**Linting and formatting:**
```bash
make lint    # Run ruff and mypy checks
make format  # Format code with ruff
```

**Build and run:**
```bash
make build   # Build package
make run     # Start KiCad MCP server
```

**Clean up:**
```bash
make clean   # Remove build artifacts, cache files, etc.
```

## Code Architecture

This is a **Model Context Protocol (MCP) server** for KiCad that provides AI assistants with access to KiCad projects and operations. The server follows the MCP specification to expose KiCad functionality through resources, tools, and prompts.

### Core Architecture Pattern

The codebase follows a modular MCP server pattern:

- **`main.py`**: Entry point with environment loading and server startup
- **`kicad_mcp/server.py`**: FastMCP server creation and configuration
- **`kicad_mcp/config.py`**: Platform-specific configuration (macOS/Windows/Linux)
- **`kicad_mcp/context.py`**: Lifespan management and shared context

### MCP Component Organization

The server implements three types of MCP capabilities:

1. **Resources** (`kicad_mcp/resources/`): Read-only data access
   - `projects.py`: Project discovery and listing
   - `files.py`: KiCad file content access
   - `drc_resources.py`: Design rule check reports
   - `bom_resources.py`: Bill of materials data
   - `netlist_resources.py`: Circuit netlist information
   - `pattern_resources.py`: Circuit pattern recognition data

2. **Tools** (`kicad_mcp/tools/`): Interactive operations
   - `project_tools.py`: Open projects, manage workspace
   - `drc_tools.py`: Run design rule checks via KiCad CLI
   - `bom_tools.py`: Generate BOMs and component analysis
   - `analysis_tools.py`: PCB design analysis
   - `export_tools.py`: File exports and visualization
   - `schematic_edit_tools.py`: Direct schematic editing via KiCAD Skip

3. **Prompts** (`kicad_mcp/prompts/`): Template interactions
   - `templates.py`: General-purpose prompt templates
   - `drc_prompt.py`: Design rule checking workflows
   - `bom_prompts.py`: BOM analysis workflows
   - `pattern_prompts.py`: Circuit pattern recognition
   - `schematic_edit_prompts.py`: Schematic editing workflow guidance

### Key Integration Points

- **KiCad CLI Integration**: The server primarily uses `kicad-cli` for operations rather than Python APIs
- **KiCAD Skip Integration**: Uses `kicad-skip` library for direct schematic/PCB file editing via S-expression parsing
- **Cross-platform Support**: Configuration handles macOS, Windows, and Linux KiCad installations
- **Environment Configuration**: Uses `.env` files and environment variables for customization
- **Secure Operations**: Input validation and secure subprocess execution throughout

### Important Implementation Details

- **Server uses FastMCP 2.x**: Lifespan management via `functools.partial` pattern
- **Resource URIs**: Follow `kicad://` scheme (e.g., `kicad://projects`)
- **File Discovery**: Searches user-configured paths plus common project locations
- **Error Handling**: Comprehensive error handling with logging and cleanup handlers
- **Testing**: Pytest with markers for unit/integration/slow/requires_kicad/requires_kicad_skip tests

## Configuration

Environment variables are loaded from `.env` file (copy from `.env.example`):

- `KICAD_SEARCH_PATHS`: Comma-separated project directories
- `KICAD_USER_DIR`: Override default KiCad user directory
- `KICAD_APP_PATH`: Override default KiCad application path

## Testing Notes

- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
- Tests requiring KiCad CLI: `@pytest.mark.requires_kicad`
- Coverage target: 80% (configured in pyproject.toml)
- Async tests: Use `@pytest.mark.asyncio_mode = "auto"`