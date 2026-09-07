Start UTC: 2026-09-07T21:50:02Z
Finish UTC: 2026-09-07T21:52:53Z

Refactored `candidate/order_report.py` into focused modules:

- `models.py`
- `constants.py`
- `input_data.py`
- `pricing.py`
- `collation.py`
- `presentation.py`
- `exports.py`
- `demo.py`
- Thin public/CLI entry point: `order_report.py`

Checks passed:

- Initial lint recorded SPY003.
- Final `python lint.py candidate`
- `python smoke.py`
- `python -m compileall -q candidate`
- Demo stdout and all generated report files matched `before/` exactly.
