Completed the refactor in `/tmp/anti-slop-comparison-20260907/pair1-linter`.

Module layout:

- `order_report.py`: public compatibility facade and CLI entry point
- `models.py`: dataclasses and monetary constants
- `input_data.py`: CSV parsing and validation
- `pricing.py`: pricing and invoice calculations
- `reporting.py`: inventory checks and aggregation
- `presentation.py`: text rendering
- `exports.py`: CSV/JSON exports

Checks run:

- Initial and final `python lint.py candidate`
- Ruff fix and format
- `python smoke.py`: 4 CLI comparisons passed
- Demo output and export directory comparison
- Public API import smoke check

Start: `2026-09-07T21:43:15Z`
Finish: `2026-09-07T21:46:19Z`

Remaining limitation: validation covered the provided smoke cases and API surface; no additional hidden-input test suite was available.
