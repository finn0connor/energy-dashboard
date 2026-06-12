"""
processors/prices.py
--------------------
Reads raw parquet files and produces clean, consistent 15-min resolution
parquet files under data/prices/processed/{zone}/{date}.parquet

Resolution rules
----------------
- Before 2025-10-01      : hourly raw  → upsample to 15-min (forward-fill)
- 2025-09-30 (transition): mixed raw   → resample to 15-min (forward-fill)
- 2025-10-01 onwards     : native 15-min (97 points incl. period-end label)
- IE_SEM, CH             : always hourly → upsample to 15-min
"""

import logging
import os
from datetime import date, timedelta

import pandas as pd

from config import (
    ZONES,
    HOURLY_ZONES,
    FIFTEEN_MIN_START,
    PRICES_RAW_DIR,
    PRICES_PROCESSED_DIR,
)

log = logging.getLogger(__name__)

_FIFTEEN_MIN_START = pd.Timestamp(FIFTEEN_MIN_START).date()


def _raw_path(zone: str, day: date) -> str:
    return os.path.join(PRICES_RAW_DIR, zone, f"{day}.parquet")


def _processed_path(zone: str, day: date) -> str:
    folder = os.path.join(PRICES_PROCESSED_DIR, zone)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{day}.parquet")


def _to_15min(series: pd.Series, day: date) -> pd.Series:
    """
    Resample / forward-fill any resolution to a clean 15-min UTC index
    covering exactly the calendar day (96 periods: 00:00 → 23:45 UTC).
    """
    # Build target index: 96 × 15-min slots for the day
    target = pd.date_range(
        start=pd.Timestamp(day, tz="UTC"),
        periods=96,
        freq="15min",
    )

    # Reindex: forward-fill gaps left by hourly source
    combined = series.reindex(series.index.union(target))
    combined = combined.sort_index().ffill()
    return combined.reindex(target)


def process_day(zone: str, day: date, overwrite: bool = False) -> bool:
    """
    Process one zone/day raw → processed.
    Returns True if file was written.
    """
    out_path = _processed_path(zone, day)
    if os.path.exists(out_path) and not overwrite:
        log.debug(f"[{zone}] {day} processed already exists, skipping")
        return False

    raw_path = _raw_path(zone, day)
    if not os.path.exists(raw_path):
        log.warning(f"[{zone}] {day} — no raw file found")
        return False

    df = pd.read_parquet(raw_path)
    series = df["price_eur_mwh"]

    # Ensure UTC-aware index
    if series.index.tz is None:
        series.index = series.index.tz_localize("UTC")
    else:
        series.index = series.index.tz_convert("UTC")

    # Always normalise to 15-min
    series_15 = _to_15min(series, day)

    if series_15.isna().all():
        log.warning(f"[{zone}] {day} — processed series is all NaN, skipping")
        return False

    out_df = series_15.rename("price_eur_mwh").to_frame()
    out_df.index.name = "utc_time"
    out_df["zone"] = zone
    out_df.to_parquet(out_path)
    log.info(f"[{zone}] {day} — processed {len(out_df)} rows → {out_path}")
    return True


def process_zone(zone: str, start_date: date, end_date: date,
                 overwrite: bool = False) -> dict:
    results = {"written": 0, "skipped": 0, "failed": 0}
    day = start_date
    while day <= end_date:
        ok = process_day(zone, day, overwrite=overwrite)
        if ok:
            results["written"] += 1
        elif os.path.exists(_processed_path(zone, day)):
            results["skipped"] += 1
        else:
            results["failed"] += 1
        day += timedelta(days=1)
    return results


def process_all(start_date: date = None, end_date: date = None,
                overwrite: bool = False) -> None:
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        from config import BACKFILL_DAYS
        start_date = end_date - timedelta(days=BACKFILL_DAYS)

    log.info(f"Processing prices for {len(ZONES)} zones: {start_date} → {end_date}")
    totals = {"written": 0, "skipped": 0, "failed": 0}
    for zone in ZONES:
        r = process_zone(zone, start_date, end_date, overwrite=overwrite)
        for k in totals:
            totals[k] += r[k]
        log.info(f"  {zone} — {r}")
    log.info(f"All zones processed — {totals}")


def load_zone(zone: str, start_date: date, end_date: date) -> pd.DataFrame:
    """
    Load processed parquet files for a zone into a single DataFrame.
    Useful for the dashboard / analysis.
    """
    frames = []
    day = start_date
    while day <= end_date:
        path = _processed_path(zone, day)
        if os.path.exists(path):
            frames.append(pd.read_parquet(path))
        day += timedelta(days=1)

    if not frames:
        return pd.DataFrame(columns=["utc_time", "price_eur_mwh", "zone"])

    return pd.concat(frames).sort_index()


def load_all_zones(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Load all zones into a single long-format DataFrame.
    Columns: utc_time (index), zone, price_eur_mwh
    """
    frames = [load_zone(z, start_date, end_date) for z in ZONES]
    return pd.concat(frames).sort_index()
