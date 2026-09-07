Refactored `candidate/order_report.py` into cohesive modules:

- `models.py`
- `input_data.py`
- `pricing.py`
- `aggregation.py`
- `presentation.py`
- `exports.py`
- `order_report.py` remains the public import and CLI entry point.

Checks run:

- `python -m ruff format candidate`
- `python smoke.py`
- Public API symbol check
- Demo report and export parity checks
- `python -m py_compile candidate/*.py`

Start UTC: `2026-09-07T21:46:50Z`
Finish UTC: `2026-09-07T21:49:08Z`

No known limitations.
