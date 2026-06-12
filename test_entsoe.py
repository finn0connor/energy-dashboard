import os
from dotenv import load_dotenv
from entsoe import EntsoePandasClient
import pandas as pd

load_dotenv()

client = EntsoePandasClient(api_key=os.getenv("ENTSOE_TOKEN"))

start = pd.Timestamp("2026-06-12", tz="UTC")
end   = start + pd.Timedelta(days=1)

# GB alternatives
gb_zones = {
    "GB":           "10YGB----------A",
    "GB_NIR":       "10Y1001A1001A016",
    "GB_GBN":       "10Y1001A1001A013",
}

# Italy has multiple bidding zones
it_zones = {
    "IT_N":         "10YIT-GRTN-----B",
    "IT_NORD":      "10Y1001A1001A73I",
    "IT_CNORD":     "10Y1001A1001A70O",
    "IT_CSUD":      "10Y1001A1001A71M",
    "IT_SUD":       "10Y1001A1001A788",
    "IT_SICI":      "10Y1001A1001A75E",
    "IT_SARD":      "10Y1001A1001A74G",
    "IT_CALA":      "10Y1001A1001A72K",
    "IT_ROSN":      "10Y1001A1001A77A",
}

print("=== GB ===")
for name, eic in gb_zones.items():
    try:
        df = client.query_day_ahead_prices(eic, start=start, end=end)
        print(f"  OK  {name:12s} ({eic}) — {len(df)} prices, freq={pd.infer_freq(df.index)}")
    except Exception as e:
        print(f" FAIL  {name:12s} ({eic}) — {type(e).__name__}")

print("\n=== Italy ===")
for name, eic in it_zones.items():
    try:
        df = client.query_day_ahead_prices(eic, start=start, end=end)
        print(f"  OK  {name:12s} ({eic}) — {len(df)} prices, freq={pd.infer_freq(df.index)}")
    except Exception as e:
        print(f" FAIL  {name:12s} ({eic}) — {type(e).__name__}")
