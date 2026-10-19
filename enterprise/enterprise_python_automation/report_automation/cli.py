"""Command-line entry point."""
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from report_automation.report import generate_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="report-automation",
        description="Generate PDF reports from CSV data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report", help="Generate a report once.")
    report_parser.add_argument("--input", default="data/sample_data.csv", help="Input CSV path")
    report_parser.add_argument("--output", default=None, help="Output PDF path")

    schedule_parser = subparsers.add_parser("schedule", help="Generate a report repeatedly.")
    schedule_parser.add_argument("--input", default="data/sample_data.csv", help="Input CSV path")
    schedule_parser.add_argument("--output-dir", default="output", help="Output directory")
    schedule_parser.add_argument("--interval", type=int, default=60, help="Interval in minutes (default: 60)")

    args = parser.parse_args()
    if args.command == "report":
        output = args.output or f"output/report_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        try:
            summary = generate_pdf(args.input, output)
            logger.info("Report created: %s", Path(output).resolve())
            logger.info("Records: %s | Total: %.2f | Average: %.2f",
                        summary["count"], summary["total"], summary["average"])
        except (OSError, ValueError) as exc:
            logger.error("%s", exc)
            raise SystemExit(1) from exc
    elif args.command == "schedule":
        if args.interval < 1:
            parser.error("--interval must be at least 1 minute")
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                output = Path(args.output_dir) / f"report_{datetime.now():%Y%m%d_%H%M%S}.pdf"
                try:
                    summary = generate_pdf(args.input, output)
                    logger.info("Created %s (%d records)", output, summary["count"])
                except (OSError, ValueError) as exc:
                    logger.error("Report generation failed: %s", exc)
                time.sleep(args.interval * 60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
