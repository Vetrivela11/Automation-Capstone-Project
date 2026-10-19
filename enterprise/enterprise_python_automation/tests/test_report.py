
import pytest
from report_automation.report import read_csv, summarize, generate_pdf


def test_summarize_totals():
    rows = [
        {"date": "2026-01-01", "category": "Sales", "amount": 10.0},
        {"date": "2026-01-02", "category": "Sales", "amount": 20.0},
        {"date": "2026-01-03", "category": "Support", "amount": 5.0},
    ]
    result = summarize(rows)
    assert result["count"] == 3
    assert result["total"] == 35.0
    assert result["average"] == pytest.approx(35 / 3)
    assert result["category_totals"] == {
        "Sales": 30.0,
        "Support": 5.0,
    }


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        read_csv("this-file-does-not-exist.csv")


def test_invalid_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("name,value\nA,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CSV must contain"):
        read_csv(path)


def test_generate_pdf(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text(
        "date,category,amount\n2026-01-01,Sales,100\n",
        encoding="utf-8",
    )
    target = tmp_path / "out" / "report.pdf"
    result = generate_pdf(source, target)

    assert target.exists()
    assert target.stat().st_size > 0
    assert result["total"] == 100.0
