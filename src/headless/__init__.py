r"""Offscreen UI automation. All modules support Python 3.8 and newer.

Entry point: python main.py --headless --help

The widgets mode preserves argument order, including repeated arguments:

    --headless --mode widgets
    --set input.line_input BV...
    --click input.button_next
    --get confirm.text_info
    --click confirm.button_next
    --set selection.line_selection 1-3
    --click selection.button_setSelection
    --click selection.button_next
    --set config.line_path D:\\Videos
    --set config.table_downloads[1,1] true
    --click config.button_submit

The download mode builds the same operations instead of bypassing the UI:

    --headless --mode download --url BV... --episodes 1-3
    --path D:\\Videos --quality 80 --codec hevc --danmaku true --download

Queries are explicit: --get returns a value, --inspect returns widget metadata,
and --list-controls discovers object names. Reads can target inactive pages;
writes require an active, enabled, writable control. Table coordinates and task
ordinals are one-based. Task IDs remain stable even after cleaning the UI list.
--wait TARGET PROPERTY VALUE compares a property with a JSON value or string.
--wait-downloads waits silently; a final result is emitted once at shutdown.

All output, including errors and diagnostics, is JSON Lines on stdout. Configuration
and login credentials are read from the normal GUI configuration location;
changes never persist. There is no interactive stdin protocol, login mutation,
pause operation, arbitrary Python evaluation, or external GUI launching.

Extension points:
* Controls.register_page: lazy page provider and logical active-page predicate.
* AdapterRegistry.register: typed widget reader and optional value writer.
* Runner.register_operation: explicit operation handler.
* business.build_operations: shortcuts compiled into the shared operation model.

New CLI operations should be declared in cli.parse and registered with Runner.
New async pages also need a readiness predicate (Runner.register_readiness).
Keep task waiting and shutdown centralized rather than starting another loop.
"""
