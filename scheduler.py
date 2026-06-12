"""
scheduler.py
------------
Orchestrates daily fetching and processing of all price data.

Usage
-----
  # Backfill last 90 days then process:
  python scheduler.py --backfill

  # Fetch and process today only:
  python scheduler.py --today

  # Fetch and process a specific date range:
  python scheduler.py --start 2025-01-01 --end 2025-06-12

  # Re-fetch and reprocess everything (overwrite):
  python scheduler.py --backfill --overwrite
"""

import argparse
import logging
from datetime import date, timedelta

from fetchers.prices import fetch_all
from processors.prices import process_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run(start_date: date, end_date: date, overwrite: bool = False) -> None:
    log.info(f"=== FETCH  {start_date} → {end_date} ===")
    fetch_all(start_date=start_date, end_date=end_date, overwrite=overwrite)

    log.info(f"=== PROCESS {start_date} → {end_date} ===")
    process_all(start_date=start_date, end_date=end_date, overwrite=overwrite)

    log.info("=== DONE ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Energy dashboard price scheduler")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backfill", action="store_true",
                       help="Fetch last BACKFILL_DAYS days (default 90)")
    group.add_argument("--today", action="store_true",
                       help="Fetch today only")
    parser.add_argument("--start", type=date.fromisoformat,
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end",   type=date.fromisoformat,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-fetch and reprocess even if files exist")
    args = parser.parse_args()

    today = date.today()

    if args.today:
        run(today, today, overwrite=args.overwrite)
    elif args.backfill:
        from config import BACKFILL_DAYS
        run(today - timedelta(days=BACKFILL_DAYS), today, overwrite=args.overwrite)
    elif args.start:
        end = args.end or today
        run(args.start, end, overwrite=args.overwrite)
    else:
        # Default: just today
        run(today, today, overwrite=args.overwrite)
