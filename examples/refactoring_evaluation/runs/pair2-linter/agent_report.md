Completed the linter refactor in `/tmp/anti-slop-comparison-20260907/pair2-linter`.

Final layout:

- `candidate/models.py` — data classes and monetary constants
- `candidate/input_data.py` — CSV reading and validation
- `candidate/pricing.py` — pricing and stock checks
- `candidate/reporting.py` — report assembly, aggregates, and text rendering
- `candidate/exports.py` — CSV, JSON, and filesystem exports
- `candidate/order_report.py` — public API facade and CLI entry point

Checks run:

- Initial lint: `SPY003` at 554 lines
- `ruff format candidate`
- `smoke.py`: 4 CLI comparisons passed
- Final `lint.py candidate`: passed with no diagnostics
- Direct export comparison against `before`: passed

UTC timing: start `2026-09-07T21:46:50Z`; finish `2026-09-07T21:49:26Z`.

Remaining limitation: internal modules use direct imports so the facade remains directly executable as required; package-style import under a containing package is not supported.
