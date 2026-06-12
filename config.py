import os
from dotenv import load_dotenv

load_dotenv()

ENTSOE_TOKEN = os.getenv("ENTSOE_TOKEN", "")

# Date from which 15-min pricing began (except IE_SEM, CH which remain hourly)
FIFTEEN_MIN_START = "2025-10-01"
TRANSITION_DATE   = "2025-09-30"

# Zones that remain hourly indefinitely
HOURLY_ZONES = {"IE_SEM", "CH"}

ZONES = {
    # British Isles
    "IE_SEM": "10Y1001A1001A59C",

    # Western Europe
    "FR":     "10YFR-RTE------C",
    "NL":     "10YNL----------L",
    "BE":     "10YBE----------2",
    "ES":     "10YES-REE------0",
    "PT":     "10YPT-REN------W",
    "DE_LU":  "10Y1001A1001A82H",
    "CH":     "10YCH-SWISSGRIDZ",
    "AT":     "10YAT-APG------L",

    # Italy
    "IT_NORD":  "10Y1001A1001A73I",
    "IT_CNORD": "10Y1001A1001A70O",
    "IT_CSUD":  "10Y1001A1001A71M",
    "IT_SUD":   "10Y1001A1001A788",
    "IT_SICI":  "10Y1001A1001A75E",
    "IT_SARD":  "10Y1001A1001A74G",

    # Nordics
    "NO1":    "10YNO-1--------2",
    "NO2":    "10YNO-2--------T",
    "NO3":    "10YNO-3--------J",
    "NO4":    "10YNO-4--------9",
    "NO5":    "10Y1001A1001A48H",
    "SE1":    "10Y1001A1001A44P",
    "SE2":    "10Y1001A1001A45N",
    "SE3":    "10Y1001A1001A46L",
    "SE4":    "10Y1001A1001A47J",
    "DK1":    "10YDK-1--------W",
    "DK2":    "10YDK-2--------M",
    "FI":     "10YFI-1--------U",

    # Central & Eastern Europe
    "PL":     "10YPL-AREA-----S",
    "CZ":     "10YCZ-CEPS-----N",
    "SK":     "10YSK-SEPS-----K",
    "HU":     "10YHU-MAVIR----U",
    "RO":     "10YRO-TEL------P",
    "SI":     "10YSI-ELES-----O",
    "HR":     "10YHR-HEP------M",
    "RS":     "10YCS-SERBIATSOV",
    "BG":     "10YCA-BULGARIA-R",
    "GR":     "10YGR-HTSO-----Y",
}

# How many days of history to backfill on first run
BACKFILL_DAYS = 90

# Data paths
DATA_DIR             = "data"
PRICES_RAW_DIR       = "data/prices/raw"
PRICES_PROCESSED_DIR = "data/prices/processed"
