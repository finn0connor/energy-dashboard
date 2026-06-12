"""
fetchers/prices.py
------------------
Pulls day-ahead prices from ENTSO-E for one zone / one date and saves
the raw Series as a parquet file under data/prices/raw/{zone}/{date}.parquet
"""

import logging
import os
import time
from datetime import date, timedelta

import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError

from config import (
    ENTSOE_TOKEN,
    ZONES,
    PRICES_RAW_DIR,
    BACKFILL_DAYS,
)

log = logging.getLogger(__name__)

client = EntsoePandasClient(api_key=ENTSOE_TOKEN)


def _raw_path(zone: str, day: date) -> str:
    folder = os.path.join(PRICES_RAW_DIR, zone)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{day}.parquet")


def fetch_day(zone: str, day: date, overwrite: bool = False) -> bool:
    """
    Fetch prices for one zone/day and save to parquet.
    Returns True if data was saved, False if skipped or failed.
    """
    path = _raw_path(zone, day)
    if os.path.exists(path) and not overwrite:
        log.debug(f"[{zone}] {day} already exists, skipping")
        return False

    start = pd.Timestamp(day, tz="UTC")
    end   = start + pd.Timedelta(days=1)

    try:
        series = client.query_day_ahead_prices(ZONES[zone], start=start, end=end)
    except NoMatchingDataError:
        log.warning(f"[{zone}] {day} — no data from ENTSO-E")
        return False
    except Exception as e:
        log.error(f"[{zone}] {day} — unexpected error: {e}")
        return False

    if series is None or series.empty:
        log.warning(f"[{zone}] {day} — empty response")
        return False

    df = series.rename("price_eur_mwh").to_frame()
    df.index.name = "utc_time"
    df.to_parquet(path)
    log.info(f"[{zone}] {day} — saved {len(df)} rows → {path}")
    return True


def fetch_zone(zone: str, start_date: date, end_date: date,
               overwrite: bool = False, sleep_s: float = 0.5) -> dict:
    """
    Fetch all days in [start_date, end_date] for a single zone.
    Returns a summary dict.
    """
    results = {"saved": 0, "skipped": 0, "failed": 0}
    day = start_date
    while day <= end_date:
        ok = fetch_day(zone, day, overwrite=overwrite)
        if ok:
            results["saved"] += 1
        elif os.path.exists(_raw_path(zone, day)):
            results["skipped"] += 1
        else:
            results["failed"] += 1
        day += timedelta(days=1)
        time.sleep(sleep_s)
    return results


def fetch_all(start_date: date = None, end_date: date = None,
              overwrite: bool = False) -> None:
    """
    Fetch all zones for the given date range.
    Defaults to today and the last BACKFILL_DAYS days.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=BACKFILL_DAYS)

    log.info(f"Fetching prices for {len(ZONES)} zones: {start_date} → {end_date}")

    totals = {"saved": 0, "skipped": 0, "failed": 0}
    for zone in ZONES:
        log.info(f"  Zone: {zone}")
        r = fetch_zone(zone, start_date, end_date, overwrite=overwrite)
        for k in totals:
            totals[k] += r[k]
        log.info(f"  {zone} done — {r}")

    log.info(f"All zones complete — {totals}")
