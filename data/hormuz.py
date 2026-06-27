#Making hormuz.py
#It extracts data 

#Importing the packages 
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone



def load_hormuz_data(json_path: str = "hormuz_data.json") -> dict:
    
    # Open and read the JSON
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Could not find {json_path}. Run website_scraper.py first.")

    with open(json_path, "r") as file:
        data = json.load(file)

    # Step 1 — Confirm dashboard API was used (most reliable source)
    if not data.get("dashboard_api_used", False):
        raise ValueError(
            "dashboard_api_used is False in the JSON. "
            "The scraper did not get API data. Re-run website_scraper.py."
        )

    # Navigate to the api data — it lives inside pages[0]["dashboard_api"]
    api = data["pages"][0]["dashboard_api"]

    # Run all extraction steps
    metrics    = {}
    timeseries = {}

    _extract_strait_status(api, metrics)
    _extract_ship_metrics(api, metrics)
    _extract_oil_price(api, metrics, timeseries)
    _extract_insurance(api, metrics)
    _extract_throughput(api, metrics, timeseries)
    _extract_tanker_rates(api, metrics, timeseries)
    _extract_trade_impact(api, metrics)
    _extract_diplomacy(api, metrics)
    timeline = _extract_crisis_timeline(api)

    print("[hormuz.py] Data loaded successfully.")
    print(f"[hormuz.py] Strait status : {metrics.get('strait_status')}")
    print(f"[hormuz.py] Brent price   : ${metrics.get('brent_price')}")
    print(f"[hormuz.py] Transits today: {metrics.get('transits_today')}")

    return {
        "metrics":    metrics,
        "timeseries": timeseries,
        "timeline":   timeline
    }


# ── Step 2: Strait Status ──────────────────────────────────────────────────────
def _extract_strait_status(api: dict, metrics: dict) -> None:
    """
    Extracts strait open/closed/restricted status.
    Always uses dashboard_api source — more reliable than DOM text.
    """
    strait = api.get("straitStatus", {})

    metrics["strait_status"]      = strait.get("status", "UNKNOWN")
    metrics["strait_since"]       = strait.get("since", "Unknown")
    metrics["strait_description"] = strait.get("description", "")

    # Calculate how many days the crisis has been ongoing
    try:
        since_date = datetime.strptime(metrics["strait_since"], "%Y-%m-%d")
        metrics["strait_duration_days"] = (datetime.now() - since_date).days
    except Exception:
        metrics["strait_duration_days"] = None

    print(f"[hormuz.py] Strait status extracted: {metrics['strait_status']} since {metrics['strait_since']}")


# ── Step 3: Ship & Vessel Metrics ──────────────────────────────────────────────
def _extract_ship_metrics(api: dict, metrics: dict) -> None:
    """
    Extracts ship transit counts and stranded vessel data.
    """
    ship    = api.get("shipCount", {})
    stranded = api.get("strandedVessels", {})

    # Ship counts
    metrics["transits_today"]       = ship.get("currentTransits", None)
    metrics["transits_last_24h"]    = ship.get("last24h", None)
    metrics["transits_normal_daily"]= ship.get("normalDaily", 60)
    metrics["transits_pct_normal"]  = ship.get("percentOfNormal", None)

    # Stranded vessels — tankers most relevant for oil companies
    metrics["stranded_total"]       = stranded.get("total", None)
    metrics["stranded_tankers"]     = stranded.get("tankers", None)
    metrics["stranded_bulk"]        = stranded.get("bulk", None)
    metrics["stranded_other"]       = stranded.get("other", None)
    metrics["stranded_change_today"]= stranded.get("changeToday", None)

    print(f"[hormuz.py] Ship metrics extracted: {metrics['transits_today']} transits today, {metrics['stranded_tankers']} tankers stranded")


# ── Step 4: Oil Price + Sparkline ─────────────────────────────────────────────
def _extract_oil_price(api: dict, metrics: dict, timeseries: dict) -> None:
    """
    Extracts current Brent crude price and converts the 24-point
    sparkline array into a proper DataFrame with a date index.
    """
    oil = api.get("oilPrice", {})

    # Current price metrics
    metrics["brent_price"]          = oil.get("brentPrice", None)
    metrics["brent_change_24h"]     = oil.get("change24h", None)
    metrics["brent_change_pct_24h"] = oil.get("changePercent24h", None)

    # Sparkline → DataFrame
    # The sparkline has 24 data points, each representing one day going back
    sparkline = oil.get("sparkline", [])
    if sparkline:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        n = len(sparkline)
        # Generate date index going back n days from today
        dates = [today - timedelta(days=(n - 1 - i)) for i in range(n)]

        df_spark = pd.DataFrame({
            "date":        dates,
            "brent_price": sparkline
        })
        df_spark = df_spark.set_index("date")

        # Calculate daily returns from sparkline
        df_spark["daily_return"]  = df_spark["brent_price"].pct_change() * 100
        df_spark["volatility_7d"] = df_spark["daily_return"].rolling(window=7, min_periods=2).std()

        timeseries["brent_sparkline"] = df_spark
        print(f"[hormuz.py] Brent sparkline: {n} data points, ${sparkline[0]} → ${sparkline[-1]}")
    else:
        timeseries["brent_sparkline"] = pd.DataFrame()
        print("[hormuz.py] WARNING: No sparkline data found.")


# ── Step 5: Insurance ──────────────────────────────────────────────────────────
def _extract_insurance(api: dict, metrics: dict) -> None:
    """
    Extracts war risk insurance data.
    The multiplier shows how many times above normal rates currently are.
    """
    insurance = api.get("insurance", {})

    metrics["insurance_level"]       = insurance.get("level", "UNKNOWN")
    metrics["insurance_war_risk_pct"]= insurance.get("warRiskPercent", None)
    metrics["insurance_normal_pct"]  = insurance.get("normalPercent", None)
    metrics["insurance_multiplier"]  = insurance.get("multiplier", None)

    print(f"[hormuz.py] Insurance multiplier: {metrics['insurance_multiplier']}x normal")


# ── Step 6: Throughput + 7-day series ─────────────────────────────────────────
def _extract_throughput(api: dict, metrics: dict, timeseries: dict) -> None:
    """
    Extracts throughput data and converts the 7-day array into a DataFrame.
    DWT = Deadweight Tonnage (how much cargo is actually moving through)
    """
    throughput = api.get("throughput", {})

    metrics["throughput_today_dwt"]    = throughput.get("todayDWT", None)
    metrics["throughput_average_dwt"]  = throughput.get("averageDWT", None)
    metrics["throughput_pct_normal"]   = throughput.get("percentOfNormal", None)

    # last7Days array → DataFrame
    last_7 = throughput.get("last7Days", [])
    if last_7:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        dates = [today - timedelta(days=(6 - i)) for i in range(7)]

        df_throughput = pd.DataFrame({
            "date":       dates,
            "throughput_dwt": last_7
        })
        df_throughput = df_throughput.set_index("date")

        # Calculate day-over-day % change
        df_throughput["pct_change"] = df_throughput["throughput_dwt"].pct_change() * 100

        timeseries["throughput_7d"] = df_throughput
        print(f"[hormuz.py] Throughput 7-day series extracted: {last_7[0]:,} → {last_7[-1]:,} DWT")
    else:
        timeseries["throughput_7d"] = pd.DataFrame()


# ── Step 7: Tanker Rates + trend ──────────────────────────────────────────────
def _extract_tanker_rates(api: dict, metrics: dict, timeseries: dict) -> None:
    """
    Extracts tanker rate data and converts the trend array into a DataFrame.
    Rates in Worldscale (WS) points for AG-East (TD3C) VLCC route.
    """
    rates = api.get("tankerRates", {})

    metrics["tanker_rate_current"]     = rates.get("currentRate", None)
    metrics["tanker_rate_pre_crisis"]  = rates.get("preCrisisRate", None)
    metrics["tanker_rate_change_pct"]  = rates.get("changePercent", None)
    metrics["tanker_rate_route"]       = rates.get("route", "AG-East (TD3C)")
    metrics["tanker_rate_vessel_type"] = rates.get("vesselType", "VLCC")

    # Trend array → DataFrame
    trend = rates.get("trend", [])
    if trend:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        n = len(trend)
        dates = [today - timedelta(days=(n - 1 - i)) for i in range(n)]

        df_rates = pd.DataFrame({
            "date":        dates,
            "tanker_rate": trend
        })
        df_rates = df_rates.set_index("date")
        timeseries["tanker_rates_7d"] = df_rates
        print(f"[hormuz.py] Tanker rates extracted: WS{trend[0]} → WS{trend[-1]} ({metrics['tanker_rate_change_pct']}% vs pre-crisis)")
    else:
        timeseries["tanker_rates_7d"] = pd.DataFrame()


# ── Step 8: Global Trade Impact ───────────────────────────────────────────────
def _extract_trade_impact(api: dict, metrics: dict) -> None:
    """
    Extracts global trade impact figures.
    These feed into the LLM prompt as macroeconomic context.
    """
    impact = api.get("globalTradeImpact", {})

    metrics["pct_world_oil_at_risk"]      = impact.get("percentOfWorldOilAtRisk", None)
    metrics["daily_cost_billions"]         = impact.get("estimatedDailyCostBillions", None)
    metrics["pct_world_lng_at_risk"]       = impact.get("lngImpact", {}).get("percentOfWorldLngAtRisk", None)
    metrics["shipping_rate_increase_pct"]  = impact.get("supplyChainImpact", {}).get("shippingRateIncreasePercent", None)
    metrics["consumer_price_impact_pct"]   = impact.get("supplyChainImpact", {}).get("consumerPriceImpactPercent", None)

    # Alternative routes being used — useful context for LLM
    alt_routes = impact.get("alternativeRoutes", [])
    metrics["alternative_routes"] = [r.get("name") for r in alt_routes if r.get("name")]

    print(f"[hormuz.py] Trade impact: {metrics['pct_world_oil_at_risk']}% of world oil at risk, ${metrics['daily_cost_billions']}B/day cost")


# ── Step 9: Diplomacy Status ───────────────────────────────────────────────────
def _extract_diplomacy(api: dict, metrics: dict) -> None:
    """
    Extracts current diplomatic status.
    This explains WHY prices may be moving — critical LLM context.
    """
    diplomacy = api.get("diplomacy", {})

    metrics["diplomacy_status"]   = diplomacy.get("status", "UNKNOWN")
    metrics["diplomacy_headline"] = diplomacy.get("headline", "")
    metrics["diplomacy_summary"]  = diplomacy.get("summary", "")
    metrics["diplomacy_date"]     = diplomacy.get("date", "")
    metrics["diplomacy_parties"]  = diplomacy.get("parties", [])

    print(f"[hormuz.py] Diplomacy status: {metrics['diplomacy_status']} ({metrics['diplomacy_date']})")


# ── Step 10: Crisis Timeline ───────────────────────────────────────────────────
def _extract_crisis_timeline(api: dict) -> pd.DataFrame:
    """
    Extracts the crisis timeline events into a clean sorted DataFrame.
    Used to overlay event markers on stock price charts.
    """
    timeline_data = api.get("crisisTimeline", {})
    events        = timeline_data.get("events", [])

    if not events:
        print("[hormuz.py] WARNING: No crisis timeline events found.")
        return pd.DataFrame(columns=["date", "title", "type", "description"])

    rows = []
    for event in events:
        rows.append({
            "date":        pd.to_datetime(event.get("date"), utc=True),
            "title":       event.get("title", ""),
            "type":        event.get("type", ""),
            "description": event.get("description", "")
        })

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    print(f"[hormuz.py] Crisis timeline: {len(df)} events extracted.")
    return df


# ── Main (test run) ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = load_hormuz_data("hormuz_data.json")

    print("\n── METRICS ──")
    for k, v in result["metrics"].items():
        print(f"  {k}: {v}")

    print("\n── TIMESERIES KEYS ──")
    for k, df in result["timeseries"].items():
        print(f"  {k}: {len(df)} rows")

    print("\n── CRISIS TIMELINE ──")
    print(result["timeline"][["date", "type", "title"]])