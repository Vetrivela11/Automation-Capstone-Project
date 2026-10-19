"""CSV analysis and PDF report generation."""
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def read_csv(csv_path: str | Path) -> list[dict]:
    """Load CSV rows and validate the required columns."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"date", "category", "amount"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV must contain these columns: date, category, amount")
        rows = []
        for line_number, row in enumerate(reader, start=2):
            try:
                amount = float(row["amount"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid amount on CSV line {line_number}") from exc
            rows.append({
                "date": row["date"],
                "category": row["category"].strip() or "Uncategorized",
                "amount": amount,
            })
    if not rows:
        raise ValueError("Input CSV contains no data rows.")
    return rows


def summarize(rows: list[dict]) -> dict:
    """Calculate total, average, count, and category totals."""
    total = sum(row["amount"] for row in rows)
    category_totals = defaultdict(float)
    for row in rows:
        category_totals[row["category"]] += row["amount"]
    return {
        "count": len(rows),
        "total": total,
        "average": total / len(rows),
        "category_totals": dict(sorted(category_totals.items())),
    }


def generate_pdf(csv_path: str | Path, output_path: str | Path) -> dict:
    """Generate a formatted PDF report and return its summary."""
    rows = read_csv(csv_path)
    summary = summarize(rows)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    story = [
        Paragraph("Enterprise Automated Data Report", styles["Title"]),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
        Spacer(1, 8 * mm),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(f"Records processed: {summary['count']}", styles["BodyText"]),
        Paragraph(f"Total amount: {summary['total']:,.2f}", styles["BodyText"]),
        Paragraph(f"Average amount: {summary['average']:,.2f}", styles["BodyText"]),
        Spacer(1, 5 * mm),
        Paragraph("Totals by Category", styles["Heading2"]),
    ]
    category_data = [["Category", "Total Amount"]]
    category_data += [[name, f"{amount:,.2f}"] for name, amount in summary["category_totals"].items()]
    category_table = Table(category_data, colWidths=[85 * mm, 55 * mm], repeatRows=1)
    category_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183153")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3F8")]),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([category_table, Spacer(1, 7 * mm), Paragraph("Transaction Details", styles["Heading2"])])
    detail_data = [["Date", "Category", "Amount"]]
    detail_data += [[r["date"], r["category"], f"{r['amount']:,.2f}"] for r in rows]
    detail_table = Table(detail_data, colWidths=[40 * mm, 65 * mm, 35 * mm], repeatRows=1)
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F6B55")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F5")]),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    doc.build(story)
    return summary
