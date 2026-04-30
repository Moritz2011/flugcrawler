#!/usr/bin/env python3
"""
Flugpreis-Crawler: NUE -> PMI / PMI -> NUE
Kombinationen werden automatisch aus dem Reisezeitraum generiert.
"""

import json
import sys
import time
import traceback
from datetime import datetime, date, timedelta
from pathlib import Path

# UTF-8 Ausgabe sicherstellen (wichtig fuer GitHub Actions / Linux)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests

# =============================================================================
#  Konfiguration
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_FILE  = SCRIPT_DIR / "flight_data.json"
DASHBOARD  = SCRIPT_DIR / "index.html"

# Reisezeitraum: fruehester Hinflug bis spaetester Rueckflug
TRAVEL_START = date(2026, 10, 22)
TRAVEL_END   = date(2026, 10, 26)
MIN_NIGHTS   = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# =============================================================================
#  Kombinationen automatisch generieren
# =============================================================================

def build_combinations():
    """
    Generiert alle Hin/Rueck-Kombinationen im Reisefenster
    mit mindestens MIN_NIGHTS Naechten.
    """
    combos = []
    out = TRAVEL_START
    while out <= TRAVEL_END:
        ret = out + timedelta(days=MIN_NIGHTS)
        while ret <= TRAVEL_END:
            combos.append({
                "out":    out.strftime("%Y-%m-%d"),
                "ret":    ret.strftime("%Y-%m-%d"),
                "nights": (ret - out).days,
            })
            ret += timedelta(days=1)
        out += timedelta(days=1)
    return combos

COMBINATIONS   = build_combinations()
OUTBOUND_DATES = sorted(set(c["out"] for c in COMBINATIONS))
RETURN_DATES   = sorted(set(c["ret"] for c in COMBINATIONS))

# =============================================================================
#  Airline-APIs
# =============================================================================

def fetch_ryanair(dep, arr, dates):
    results = {}
    for d in dates:
        try:
            r = requests.get(
                "https://www.ryanair.com/api/farfnd/v4/oneWayFares",
                params={
                    "departureAirportIataCode":  dep,
                    "arrivalAirportIataCode":    arr,
                    "outboundDepartureDateFrom": d,
                    "outboundDepartureDateTo":   d,
                    "currency": "EUR",
                },
                headers=HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                for fare in r.json().get("fares", []):
                    fd = fare["outbound"]["departureDate"][:10]
                    fp = fare["outbound"]["price"]["value"]
                    if fp and fp > 0:
                        if fd not in results or fp < results[fd]["price"]:
                            results[fd] = {"price": round(fp, 2), "airline": "Ryanair"}
            time.sleep(0.5)
        except Exception as e:
            print(f"  Ryanair {dep}->{arr} {d}: {e}")
    return results


def fetch_eurowings(dep, arr, dates):
    results = {}
    session = requests.Session()
    # Session-Cookies holen
    try:
        session.get(
            "https://www.eurowings.com/de.html",
            headers=HEADERS,
            timeout=10,
        )
    except Exception:
        pass

    for d in dates:
        # Versuch 1: cheapestfares-Endpunkt
        try:
            r = session.get(
                "https://www.eurowings.com/api/ndsservices/shoppingbasket/"
                "v1.0.0/flightoffers/cheapestfares",
                params={
                    "departureAirport": dep,
                    "arrivalAirport":   arr,
                    "travelDate":       d,
                    "currency":         "EUR",
                    "cabinClass":       "ECONOMY",
                    "passengerTypes":   "ADULT",
                },
                headers={**HEADERS, "Referer": "https://www.eurowings.com/"},
                timeout=15,
            )
            if r.status_code == 200:
                for offer in r.json().get("flightOffers", []):
                    fd = (offer.get("departureDate") or "")[:10]
                    fp = (offer.get("price") or {}).get("amount")
                    if fd and fp and fp > 0:
                        if fd not in results or fp < results[fd]["price"]:
                            results[fd] = {"price": round(fp, 2), "airline": "Eurowings"}
            time.sleep(0.5)
        except Exception as e:
            print(f"  Eurowings {dep}->{arr} {d}: {e}")

        # Versuch 2: availability-Endpunkt als Fallback
        if d not in results:
            try:
                r2 = session.get(
                    "https://www.eurowings.com/api/v2/flightsearch/availability",
                    params={
                        "origin":          dep,
                        "destination":     arr,
                        "outboundDate":    d,
                        "adults":          1,
                        "currency":        "EUR",
                    },
                    headers={**HEADERS, "Referer": "https://www.eurowings.com/"},
                    timeout=15,
                )
                if r2.status_code == 200:
                    data = r2.json()
                    price = (
                        data.get("lowestFare")
                        or data.get("cheapestFare")
                        or (data.get("fares") or [{}])[0].get("totalPrice")
                    )
                    if price and float(price) > 0:
                        results[d] = {"price": round(float(price), 2), "airline": "Eurowings"}
                time.sleep(0.5)
            except Exception as e:
                print(f"  Eurowings v2 {dep}->{arr} {d}: {e}")
    return results


def fetch_condor(dep, arr, dates):
    results = {}
    for d in dates:
        # Versuch 1: REST-API
        try:
            r = requests.get(
                "https://www.condor.com/de/flugangebote/api/v1/flights",
                params={
                    "origin":        dep,
                    "destination":   arr,
                    "departureDate": d,
                    "adults":        1,
                    "currency":      "EUR",
                },
                headers={**HEADERS, "Referer": "https://www.condor.com/"},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                for item in data.get("flights", data.get("offers", [])):
                    fd = (item.get("departureDate") or item.get("date") or "")[:10]
                    fp = item.get("price", {}).get("amount") or item.get("totalPrice")
                    if fd and fp and float(fp) > 0:
                        if fd not in results or float(fp) < results[fd]["price"]:
                            results[fd] = {"price": round(float(fp), 2), "airline": "Condor"}
            time.sleep(0.5)
        except Exception as e:
            print(f"  Condor {dep}->{arr} {d}: {e}")
    return results


def merge_cheapest(*dicts):
    """Behaelt pro Datum nur den guenstigsten Preis aus mehreren Quellen."""
    merged = {}
    for d in dicts:
        for date_str, info in d.items():
            if date_str not in merged or info["price"] < merged[date_str]["price"]:
                merged[date_str] = info
    return merged

# =============================================================================
#  Preistrend
# =============================================================================

def get_trends(history, today):
    """
    Vergleicht heutige Preise mit dem letzten vorhandenen Tag.
    Gibt { (out_date, ret_date): {"trend": "up"|"down"|"same"|None, "diff": float} } zurueck.
    """
    prev_days = sorted(k for k in history.keys() if k < today)
    if not prev_days:
        return {}

    prev_day     = prev_days[-1]
    prev_combos  = {(c["out_date"], c["ret_date"]): c for c in history[prev_day].get("combos", [])}
    today_combos = {(c["out_date"], c["ret_date"]): c for c in history[today].get("combos", [])}

    trends = {}
    for key, tc in today_combos.items():
        pc = prev_combos.get(key)
        if tc.get("total") and pc and pc.get("total"):
            diff = round(tc["total"] - pc["total"], 2)
            if abs(diff) < 0.50:
                trends[key] = {"trend": "same", "diff": 0.0}
            elif diff > 0:
                trends[key] = {"trend": "up",   "diff": diff}
            else:
                trends[key] = {"trend": "down",  "diff": diff}
        else:
            trends[key] = {"trend": None, "diff": 0.0}
    return trends

# =============================================================================
#  HTML-Dashboard
# =============================================================================

WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def fmt_date(d):
    if not d:
        return "-"
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{WEEKDAYS_DE[dt.weekday()]} {dt.strftime('%d.%m.%Y')}"

def gf_url(out, ret):
    return (
        f"https://www.google.com/travel/flights#flt="
        f"NUE.PMI.{out}*PMI.NUE.{ret};c:EUR;e:1;sd:1;t:f"
    )

def trend_badge(t_info):
    if not t_info or t_info["trend"] is None:
        return ""
    t = t_info["trend"]
    d = abs(t_info["diff"])
    if t == "down":
        return f'<span class="trend down">&#8595; {d:.2f} &euro;</span>'
    if t == "up":
        return f'<span class="trend up">&#8593; {d:.2f} &euro;</span>'
    return '<span class="trend same">&#8594;</span>'

def generate_dashboard(history, today):
    today_data = history.get(today, {})
    combos     = today_data.get("combos", [])
    best       = today_data.get("best")
    ts         = today_data.get("timestamp", "")
    ts_display = datetime.fromisoformat(ts).strftime("%d.%m.%Y um %H:%M Uhr") if ts else "-"
    trends     = get_trends(history, today)

    hist_dates   = sorted(history.keys())[-30:]
    chart_labels = json.dumps(hist_dates)
    chart_values = json.dumps([
        history[d]["best"]["total"] if history[d].get("best") else None
        for d in hist_dates
    ])

    rows = ""
    for c in combos:
        is_best = best and c["out_date"] == best["out_date"] and c["ret_date"] == best["ret_date"]
        row_cls = ' class="best-row"' if is_best else ""
        badge   = '<span class="badge">Bestes Angebot</span>' if is_best else ""
        t_info  = trends.get((c["out_date"], c["ret_date"]))

        out_p  = (f'{c["out_price"]:.2f} &euro;<br><small>{c["out_airline"]}</small>'
                  if c["out_price"] else '<span class="na">-</span>')
        ret_p  = (f'{c["ret_price"]:.2f} &euro;<br><small>{c["ret_airline"]}</small>'
                  if c["ret_price"] else '<span class="na">-</span>')
        total  = (f'<strong>{c["total"]:.2f} &euro;</strong> {trend_badge(t_info)}'
                  if c["total"] else '<span class="na">keine Daten</span>')

        rows += f"""
        <tr{row_cls}>
          <td>{fmt_date(c["out_date"])}<br>{badge}</td>
          <td>{fmt_date(c["ret_date"])}</td>
          <td>{c["nights"]} N&auml;chte</td>
          <td>{out_p}</td>
          <td>{ret_p}</td>
          <td>{total}</td>
          <td><a href="{gf_url(c["out_date"], c["ret_date"])}" target="_blank" class="btn">Suchen</a></td>
        </tr>"""

    best_card = ""
    if best:
        t_best = trends.get((best["out_date"], best["ret_date"]))
        best_card = f"""
  <div class="best-card">
    <div class="best-label">G&uuml;nstigstes Angebot heute</div>
    <div class="best-price">{best["total"]:.2f} &euro; {trend_badge(t_best)}</div>
    <div class="best-details">
      {fmt_date(best["out_date"])} &rarr; {fmt_date(best["ret_date"])}
      &nbsp;&middot;&nbsp; {best["nights"]} N&auml;chte
      &nbsp;&middot;&nbsp; Hin: {best["out_airline"]}
      &nbsp;&middot;&nbsp; R&uuml;ck: {best["ret_airline"]}
    </div>
  </div>"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flugpreise NUE &rarr; PMI | Oktober 2026</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f4f8; color: #1a202c; }}
    .header {{ background: linear-gradient(135deg, #1a365d, #2b6cb0);
               color: white; padding: 32px 40px; }}
    .header h1 {{ font-size: 26px; font-weight: 700; }}
    .header .sub {{ opacity: .8; margin-top: 6px; font-size: 14px; }}
    .header .ts  {{ opacity: .6; margin-top: 6px; font-size: 13px; }}
    .wrap {{ max-width: 1000px; margin: 0 auto; padding: 28px 20px; }}
    .best-card {{ background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
                  border-radius: 12px; padding: 22px 28px;
                  border-left: 5px solid #38a169; margin-bottom: 24px; }}
    .best-label  {{ color: #276749; font-weight: 600; font-size: 14px; }}
    .best-price  {{ font-size: 42px; font-weight: 800; color: #22543d; margin: 6px 0 4px; }}
    .best-details{{ color: #2f855a; font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; background: white;
             border-radius: 12px; overflow: hidden;
             box-shadow: 0 2px 10px rgba(0,0,0,.08); margin-bottom: 24px; }}
    thead tr {{ background: #2b6cb0; color: white; }}
    th {{ padding: 14px 16px; text-align: left; font-size: 13px; font-weight: 600; }}
    td {{ padding: 14px 16px; font-size: 13px; vertical-align: middle;
          border-bottom: 1px solid #e2e8f0; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f7fafc; }}
    .best-row td {{ background: #f0fff4; }}
    small {{ color: #718096; display: block; margin-top: 2px; }}
    .na {{ color: #a0aec0; font-style: italic; }}
    .badge {{ background: #38a169; color: white; font-size: 10px; font-weight: 700;
              padding: 2px 8px; border-radius: 99px; display: inline-block; margin-top: 4px; }}
    .btn {{ display: inline-block; background: #2b6cb0; color: white;
            padding: 7px 14px; border-radius: 6px; text-decoration: none;
            font-size: 12px; font-weight: 500; }}
    .btn:hover {{ background: #2c5282; }}
    .trend {{ font-size: 12px; font-weight: 700; padding: 2px 7px;
              border-radius: 4px; margin-left: 6px; vertical-align: middle; }}
    .trend.down {{ background: #c6f6d5; color: #276749; }}
    .trend.up   {{ background: #fed7d7; color: #9b2c2c; }}
    .trend.same {{ background: #e2e8f0; color: #718096; }}
    .chart-box {{ background: white; border-radius: 12px; padding: 24px;
                  box-shadow: 0 2px 10px rgba(0,0,0,.08); }}
    .chart-box h3 {{ font-size: 15px; color: #2d3748; margin-bottom: 16px; }}
    canvas {{ max-height: 200px; }}
    .footer {{ text-align: center; color: #a0aec0; font-size: 12px;
               margin-top: 28px; padding-bottom: 8px; }}
  </style>
</head>
<body>
<div class="header">
  <h1>Flugpreise N&uuml;rnberg (NUE) &rarr; Mallorca (PMI)</h1>
  <div class="sub">Oktober 2026 &middot; Alle Kombinationen mit mindestens {MIN_NIGHTS} N&auml;chten</div>
  <div class="ts">Zuletzt aktualisiert: {ts_display}</div>
</div>
<div class="wrap">
  {best_card}
  <table>
    <thead>
      <tr>
        <th>Hinflug</th><th>R&uuml;ckflug</th><th>Aufenthalt</th>
        <th>Hinflug-Preis</th><th>R&uuml;ckflug-Preis</th>
        <th>Gesamt p.P.</th><th>Buchen</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="chart-box">
    <h3>Preisverlauf g&uuml;nstigste Kombination (letzte 30 Tage)</h3>
    <canvas id="chart"></canvas>
  </div>
  <div class="footer">
    Preise ohne Gew&auml;hr &middot; Direkt beim Anbieter verifizieren &middot; Automatisch generiert
  </div>
</div>
<script>
new Chart(document.getElementById('chart'), {{
  type: 'line',
  data: {{
    labels: {chart_labels},
    datasets: [{{
      label: 'Guenstigstes Angebot (EUR)',
      data: {chart_values},
      borderColor: '#2b6cb0',
      backgroundColor: 'rgba(43,108,176,0.08)',
      borderWidth: 2.5,
      pointRadius: 4,
      fill: true,
      tension: 0.3,
      spanGaps: true
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: c => c.parsed.y != null ? c.parsed.y.toFixed(2) + ' EUR' : 'keine Daten' }} }}
    }},
    scales: {{
      y: {{ ticks: {{ callback: v => v + ' EUR' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    with open(DASHBOARD, "w", encoding="utf-8") as f:
        f.write(html)

# =============================================================================
#  Hauptprogramm
# =============================================================================

def run():
    print(f"\n{'='*55}")
    print(f"  Flugpreis-Crawler  |  {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"  Kombinationen: {len(COMBINATIONS)} | Hinflugdaten: {OUTBOUND_DATES} | Rueckflugdaten: {RETURN_DATES}")
    print(f"{'='*55}")

    print("\n[1/6] Ryanair NUE -> PMI ...")
    out_ryanair   = fetch_ryanair("NUE", "PMI", OUTBOUND_DATES)
    print(f"      -> {len(out_ryanair)} Ergebnis(se)")

    print("[2/6] Eurowings NUE -> PMI ...")
    out_eurowings = fetch_eurowings("NUE", "PMI", OUTBOUND_DATES)
    print(f"      -> {len(out_eurowings)} Ergebnis(se)")

    print("[3/6] Condor NUE -> PMI ...")
    out_condor    = fetch_condor("NUE", "PMI", OUTBOUND_DATES)
    print(f"      -> {len(out_condor)} Ergebnis(se)")

    print("[4/6] Ryanair PMI -> NUE ...")
    ret_ryanair   = fetch_ryanair("PMI", "NUE", RETURN_DATES)
    print(f"      -> {len(ret_ryanair)} Ergebnis(se)")

    print("[5/6] Eurowings PMI -> NUE ...")
    ret_eurowings = fetch_eurowings("PMI", "NUE", RETURN_DATES)
    print(f"      -> {len(ret_eurowings)} Ergebnis(se)")

    print("[6/6] Condor PMI -> NUE ...")
    ret_condor    = fetch_condor("PMI", "NUE", RETURN_DATES)
    print(f"      -> {len(ret_condor)} Ergebnis(se)")

    # Guenstigster Preis je Datum aus allen Quellen
    outbound = merge_cheapest(out_ryanair, out_eurowings, out_condor)
    returns  = merge_cheapest(ret_ryanair, ret_eurowings, ret_condor)

    # Kombinationen berechnen
    combos = []
    for c in COMBINATIONS:
        out_info = outbound.get(c["out"])
        ret_info = returns.get(c["ret"])
        total    = round(out_info["price"] + ret_info["price"], 2) if (out_info and ret_info) else None
        combos.append({
            "out_date":    c["out"],
            "ret_date":    c["ret"],
            "nights":      c["nights"],
            "out_price":   out_info["price"]   if out_info else None,
            "out_airline": out_info["airline"] if out_info else None,
            "ret_price":   ret_info["price"]   if ret_info else None,
            "ret_airline": ret_info["airline"] if ret_info else None,
            "total":       total,
        })

    priced   = sorted([c for c in combos if c["total"]], key=lambda x: x["total"])
    unpriced = [c for c in combos if not c["total"]]
    combos   = priced + unpriced
    best     = priced[0] if priced else None
    today    = datetime.now().strftime("%Y-%m-%d")

    # Verlaufsdaten laden & aktualisieren
    history = {}
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            history = json.load(f)

    history[today] = {
        "combos":    combos,
        "best":      best,
        "timestamp": datetime.now().isoformat(),
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    generate_dashboard(history, today)

    print(f"\n{'='*55}")
    print(f"  Daten gespeichert  ->  {DATA_FILE.name}")
    print(f"  Dashboard erzeugt  ->  {DASHBOARD.name}")
    if best:
        print(f"\n  Bestes Angebot: {best['out_date']} -> {best['ret_date']}"
              f"  =  {best['total']:.2f} EUR")
        print(f"  ({best['out_airline']} hin / {best['ret_airline']} rueck"
              f" / {best['nights']} Naechte)")
    else:
        print("\n  Keine Preise gefunden (ggf. noch nicht buchbar).")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("\n[FEHLER] Das Script ist abgestuerzt:")
        traceback.print_exc()
        sys.exit(1)
