What’s still missing for “make me a breakout board for part X”

Datasheet parsing
• Need a tool that fetches the PDF URL (you already get it) → extracts pin-table text/CSV so the LLM can reason about pin names, functions and spacing.
• Typical libs: pdfminer.six, pymupdf or an external OCR/PDF-to-HTML service.

Symbol / footprint generation
• Either drive KiCad directly via pcbnew/schematic_editor python API, or emit Kicad-6 JSON (.kicad_kicad_sch / .kicad_mod) programmatically.
• Expose those generators as new MCP tools:
• create_symbol(pin_table, ref, footprint)
• create_pcb_footprint(...)
• place_breakout_board(symbol, connector, keepout, …).

Project-level operations
• Tool to start a blank KiCad project in a temp dir, add the new symbol & footprint, wire nets, run ERC/DRC, export Gerbers.
• Example: generate_breakout_project(mpn, connector_type, ...) -> zip.
Front-end prompt(s)
• High-level “Design breakout board” prompt template that sequences the above tools for the LLM.

Optional niceties
• 3-D model lookup (STEP) via Octopart / SnapEDA.
• Board-house DFM rules preset.