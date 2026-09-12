import csv
import io
import json
from pathlib import Path

from .models import Report
from .reporting import (
    gross_sales_by_category,
    report_discounts,
    report_tax,
    report_total,
    totals_by_customer,
    units_by_product,
)


def invoice_csv(report: Report) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(
        ["order_id", "customer_id", "date", "subtotal", "discount", "tax", "total"]
    )
    for invoice in report.invoices:
        writer.writerow(
            [
                invoice.order.identifier,
                invoice.customer.identifier,
                invoice.order.placed_on.isoformat(),
                str(invoice.subtotal),
                str(invoice.discount),
                str(invoice.tax),
                str(invoice.total),
            ]
        )
    return stream.getvalue()


def stock_csv(report: Report) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["sku", "name", "requested", "available", "shortage"])
    for alert in report.stock_alerts:
        writer.writerow(
            [
                alert.sku,
                alert.name,
                alert.requested,
                alert.available,
                alert.requested - alert.available,
            ]
        )
    return stream.getvalue()


def summary_json(report: Report) -> str:
    payload = {
        "orders": len(report.invoices),
        "total": str(report_total(report)),
        "tax": str(report_tax(report)),
        "discounts": str(report_discounts(report)),
        "customer_totals": {
            key: str(value) for key, value in totals_by_customer(report).items()
        },
        "category_gross_sales": {
            key: str(value) for key, value in gross_sales_by_category(report).items()
        },
        "units_by_product": dict(sorted(units_by_product(report).items())),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_exports(report: Report, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    from .presentation import render_report

    (directory / "report.txt").write_text(render_report(report), encoding="utf-8")
    (directory / "invoices.csv").write_text(
        invoice_csv(report), encoding="utf-8", newline=""
    )
    (directory / "stock.csv").write_text(
        stock_csv(report), encoding="utf-8", newline=""
    )
    (directory / "summary.json").write_text(summary_json(report), encoding="utf-8")
