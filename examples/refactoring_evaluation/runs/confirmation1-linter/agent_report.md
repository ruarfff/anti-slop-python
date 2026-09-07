Refactor completed in `/tmp/anti-slop-comparison-20260907/confirmation1-linter`.

Module layout:

- `order_domain.py`: data classes and constants
- `order_input.py`: CSV parsing and validation
- `order_pricing.py`: pricing and invoice creation
- `order_reporting.py`: inventory and aggregation
- `order_presentation.py`: text rendering
- `order_exports.py`: CSV, JSON, and file exports
- `order_report.py`: public re-export entry point and CLI

Checks run:

- Initial specified linter: one SPY003 diagnostic for the 554-line module.
- Ruff formatting.
- `smoke.py`: 4 CLI comparisons passed.
- Final `lint.py candidate`: passed with no diagnostics.
- Reference API output comparison: passed.
- Import from project root and direct CLI execution: passed.

Start UTC: `2026-09-07T21:57:05Z`
Finish UTC: `2026-09-07T21:59:21Z`

Remaining limitation: no dedicated test suite was provided, so verification used the supplied smoke checks and direct reference comparisons.
