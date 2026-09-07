Completed the pair3-control refactor.

Start UTC: `2026-09-07T21:49:53Z`
Finish UTC: `2026-09-07T21:51:50Z`

Final layout:

- `candidate/models.py` — data classes and monetary constants
- `candidate/parsing.py` — CSV parsing and validation
- `candidate/pricing.py` — pricing and invoice construction
- `candidate/reporting.py` — inventory checks and aggregation
- `candidate/order_report.py` — public API, presentation, exports, demo, and CLI
- `candidate/__init__.py` — package marker

Checks run:

- `python -m ruff format candidate`
- `python smoke.py` — 4 CLI comparisons passed
- Direct script execution and package import checks
- `--demo` and `--help` output comparisons passed

No known behavior limitations remain.
