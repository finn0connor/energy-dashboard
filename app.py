import os
from datetime import date, timedelta

import requests
import pandas as pd
from flask import Flask, render_template, jsonify, request

from config import ZONES
from processors.prices import load_zone

app = Flask(__name__)

DEFAULT_ZONES = ["IE_SEM", "FR", "DE_LU"]

EIRGRID_HEADERS = {
    "eirgrid-content-request": "Nextjs",
    "referer": "https://www.smartgriddashboard.com/",
}

EIRGRID_CHARTS = [
    ("wind",        "windactual,windforecast"),
    ("demand",      "demandactual,demandforecast"),
    ("generation",  "generationactual"),
    ("solar",       "solaractual,solarforecast"),
    ("frequency",   "frequency"),
    ("fuelmix",     "fuelmix"),
    ("imbalance",   "imbalancePrice,imbalanceVolume"),
]


@app.route("/")
def index():
    return render_template(
        "prices.html",
        zones=sorted(ZONES.keys()),
        default_zones=DEFAULT_ZONES,
    )


@app.route("/grid")
def grid():
    return render_template("grid.html")


@app.route("/api/prices")
def api_prices():
    zones_param = request.args.get("zones", "")
    days        = int(request.args.get("days", 3))

    requested_zones = [z.strip() for z in zones_param.split(",") if z.strip() in ZONES]
    if not requested_zones:
        return jsonify({"error": "No valid zones requested"}), 400

    end_date   = date.today()
    start_date = end_date - timedelta(days=days - 1)

    result = {}
    for zone in requested_zones:
        df = load_zone(zone, start_date, end_date)
        if df.empty:
            result[zone] = {"times": [], "prices": []}
            continue
        result[zone] = {
            "times":  df.index.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
            "prices": df["price_eur_mwh"].round(2).tolist(),
        }

    return jsonify(result)


@app.route("/api/grid")
def api_grid():
    date_str = request.args.get("date")
    if not date_str:
        date_str = date.today().strftime("%d-%b-%Y")
    else:
        try:
            d = date.fromisoformat(date_str)
            date_str = d.strftime("%d-%b-%Y")
        except ValueError:
            pass

    result = {}
    errors = []

    for chart_type, areas in EIRGRID_CHARTS:
        url = (
            "https://www.smartgriddashboard.com/api/chart/"
            f"?region=ALL&chartType={chart_type}&dateRange=day"
            f"&dateFrom={date_str}&dateTo={date_str}&areas={areas}"
        )
        try:
            resp = requests.get(url, headers=EIRGRID_HEADERS, timeout=10)
            resp.raise_for_status()
            rows = resp.json().get("Rows", [])
            result[chart_type] = rows
        except Exception as e:
            errors.append(f"{chart_type}: {str(e)}")
            result[chart_type] = []

    return jsonify({"data": result, "errors": errors, "date": date_str})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
