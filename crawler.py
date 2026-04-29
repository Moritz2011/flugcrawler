#!/usr/bin/env python3
"""
Flugpreis-Crawler: NUE → PMI / PMI → NUE (Oktober 2026)
Läuft täglich via GitHub Actions und generiert ein HTML-Dashboard (index.html).

Abgedeckte Airlines: Ryanair, Eurowings, Condor
Kombinationen: min. 2 Nächte, günstigste Kombination hervorgehoben
"""

import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# UTF-8 Ausgabe sicherstellen (wichtig für GitHub Actions / Linux)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests

# ─── Konfiguration ───────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
DATA_FILE   = SCRIPT_DIR / "flight_data.json"
DASHBOARD   = SCRIPT_DIR / "index.html"

COMBINATIONS = [
    {"out": "2026-10-22", "ret": "2026-10-24", "nights": 2},
    {"out": "2026-10-22", "ret": "2026-10-25", "nights": 3},
    {"out": "2026-10-22", "ret": "2026-10-26", "nights": 4},
    {"out": "2026-10-23", "ret": "2026-10-25", "nights": 2},
    {"out": "2026-10-23", "ret": "2026-10-26", "nights": 3},
]

OUTBOUND_DATES = sorted(set(c["out"] for c in COMBINATIONS))
RETURN_DATES   = sorted(set(c["ret"] for c in COMBINATIONS))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# ─── Ryanair API ─────────────────────────────────────────────────────────────

def fetch_ryanair(dep: str, arr: str, dates: list[str]) -> dict:
    """
    Fragt Ryanairs inoffizielle FareFinder-API ab.
    Gibt ein Dict { "YYYY-MM-DD": {"price": float, "airline": str} } zurück.
    """
    results = {}
    for date in dates:
        try:
            r = requests.get(
                "https://www.ryanair.com/api/farfnd/v4/oneWayFares",
                params={
                    "departureAirportIataCode": dep,
                    "arrivalAirportIataCode":   arr,
                    "outboundDepartureDateFrom": date,
                    "outboundDepartureDateTo":   date,
                    "currency": "EUR",
                },
                headers=HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                for fare in r.json().get("fares", []):
                    d = fare["outbound"]["departureDate"][:10]
                    p = fare["outbound"]["price"]["value"]
                    if p and p > 0:
                        if d not in results or p < results[d]["price"]:
                            results[d] = {"price": round(p, 2), "airline": "Ryanair"}
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠  Ryanair {dep}→{arr} {date}: {e}")
    return results

# ─── Eurowings API ───────────────────────────────────────────────────────────

def fetch_eurowings(dep: str, arr: str, dates: list[str]) -> dict:
    """
    Fragt Eurowings' Availability-Endpunkt ab.
    """
    results = {}
    session = requests.Session()
    # Erst die Hauptseite aufrufen, um Session-Cookies zu setzen
    try:
        session.get("https://www.eurowings.com/de.html", headers=HEADERS, timeout=10)
    except Exception:
        pass

    for date in dates:
        try:
            r = session.get(
                "https://www.eurowings.com/api/ndsservices/shoppingbasket/v1.0.0/flightoffers/cheapestfares",
                params={
                    "departureAirport": dep,
                    "arrivalAirport":   arr,
                    "travelDate":       date,
                    "currency":         "EUR",
                    "cabinClass":       "ECONOMY",
                    "passengerTypes":   "ADULT",
                },
                headers={**HEADERS, "Referer": "https://www.eurowings.com/"},
                timeout=15,
            )
            if r.status_code == 200:
                for offer in r.json().get("flightOffers", []):
                    d = (offer.get("departureDate") or "")[:10]
                    p = (offer.get("price") or {}).get("amount")
                    if d and p and p > 0:
                        if d not in results or p < results[d]["price"]:
                            results[d] = {"price": round(p, 2), "airline": "Eurowings"}
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠  Eurowings {dep}→{arr} {date}: {e}")
    return results

# ─── Condor API ──────────────────────────────────────────────────────────────

def fetch_condor(dep: str, arr: str, dates: list[str]) -> dict:
    """
    Fragt Condors Flugsuche ab.
    """
    results = {}
    for date in dates:
        try:
            r = requests.get(
                "https://www.condor.com/de/flugangebote/api/v1/flights",
                params={
                    "origin":       dep,
                    "destination":  arr,
                    "departureDate": date,
                    "adults":       1,
                    "currency":     "EUR",
                },
                headers={**HEADERS, "Referer": "https://www.condor.com/"},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                # Condor-Antwortformat kann variieren
                for item in data.get("flights", data.get("offers", [])):
                    d = (item.get("departureDate") or item.get("date") or "")[:10]
                    p = item.get("price", {}).get("amount") or item.get("totalPrice")
                    if d and p and p > 0:
                        if d not in results or p < results[d]["price"]:
                            results[d] = {"price": round(float(p), 2), "airline": "Condor"}
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠  Condor {dep}→{arr} {date}: {e}")
    return results

# ─── Preise zusammenführen ───────────────────────────────────────────────────

def merge_cheapest(*dicts) -> dict:
    """Nimmt mehrere Preis-Dicts und behält pro Datum nur den günstigsten."""
    merged = {}
    for d in dicts:
        for date, info in d.items():
            if date not in merged or info["price"] < merged[date]["price"]:
                merged[date] = info
    return merged

# ─── HTML-Dashboard ──────────────────────────────────────────────────────────

WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def fmt_date(d: str) -> str:
    if not d:
        return "—"
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{WEEKDAYS_DE[dt.weekday()]} {dt.strftime('%d.%m.%Y')}"

def google_flights_url(dep_date: str, ret_date: str) -> str:
    return (
        f"https://www.google.com/travel/flights#flt="
        f"NUE.PMI.{dep_date}*PMI.NUE.{ret_date};c:EUR;e:1;sd:1;t:f"
    )

def generate_dashboard(history: dict, today: str):
    today_data = history.get(today, {})
    combos     = today_data.get("combos", [])
    best       = today_data.get("best")
    ts         = today_data.get("timestamp", "")
    ts_display = datetime.fromisoformat(ts).strftime("%d.%m.%Y um %H:%M Uhr") if ts else "—"

    # Preisverlauf (letzte 30 Tage)
    hist_dates = sorted(history.keys())[-30:]
    chart_labels = json.dumps(hist_dates)
    chart_values = json.dumps([
        history[d]["best"]["total"] if history[d].get("best") else None
        for d in hist_dates
    ])

    # Tabellenzeilen
    rows = ""
    for c in combos:
        is_best   = best and c["out_date"] == best["out_date"] and c["ret_date"] == best["ret_date"]
        row_cls   = ' class="best-row"' if is_best else ""
        badge     = '<span class="badge">🏆 Bestes Angebot</span>' if is_best else ""
        out_p     = f'{c["out_price"]:.2f} €<br><small>{c["out_airline"]}</small>' if c["out_price"] else '<span class="na">—</span>'
        ret_p     = f'{c["ret_price"]:.2f} €<br><small>{c["ret_airline"]}</small>' if c["ret_price"] else '<span class="na">—</span>'
        total     = f'<strong>{c["total"]:.2f} €</strong>' if c["total"] else '<span class="na">keine Daten</span>'
        book_url  = google_flights_url(c["out_date"], c["ret_date"])

        rows += f"""
        <tr{row_cls}>
          <td>{fmt_date(c["out_date"])}<br>{badge}</td>
          <td>{fmt_date(c["ret_date"])}</td>
          <td>{c["nights"]} Nächte</td>
          <td>{out_p}</td>
          <td>{ret_p}</td>
          <td>{total}</td>
          <td><a href="{book_url}" target="_blank" class="btn">🔍 Suchen</a></td>
        </tr>"""

    best_card = ""
    if best:
        best_card = f"""
    <div class="best-card">
      <div class="best-label">🏆 Günstigstes Angebot heute</div>
      <div class="best-price">{best["total"]:.2f} €</div>
      <div class="best-details">
        {fmt_date(best["out_date"])} → {fmt_date(best["ret_date"])}
        &nbsp;·&nbsp; {best["nights"]} Nächte
        &nbsp;·&nbsp; Hin: {best["out_airline"]}
        &nbsp;·&nbsp; Rück: {best["ret_airline"]}
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>✈️ Flugpreise NUE → PMI | Oktober 2026</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f4f8; color: #1a202c; }}

    .header {{ background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
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
  <h1>✈️ Flugpreise Nürnberg (NUE) → Mallorca (PMI)</h1>
  <div class="sub">Oktober 2026 · Alle Kombinationen mit mindestens 2 Nächten</div>
  <div class="ts">Zuletzt aktualisiert: {ts_display}</div>
</div>
<div class="wrap">
  {best_card}
  <table>
    <thead>
      <tr>
        <th>Hinflug</th><th>Rückflug</th><th>Aufenthalt</th>
        <th>Hinflug-Preis</th><th>Rückflug-Preis</th>
        <th>Gesamt p.P.</th><th>Buchen</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="chart-box">
    <h3>📈 Preisverlauf günstigste Kombination (letzte 30 Tage)</h3>
    <canvas id="chart"></canvas>
  </div>
  <div class="footer">
    Preise ohne Gewähr · Immer direkt beim Anbieter verifizieren · Automatisch generiert
  </div>
</div>
<script>
new Chart(document.getElementById('chart'), {{
  type: 'line',
  data: {{
    labels: {chart_labels},
    datasets: [{{
      label: 'Günstigstes Angebot (€)',
      data: {chart_values},
      borderColor: '#2b6cb0',
      backgroundColor: 'rgba(43,108,176,0.08)',
      borderWidth: 2.5,
      pointRadius: 4,
      fill: true,
      tension: 0.3,
      spanGaps: true,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: c => c.parsed.y != null ? c.parsed.y.toFixed(2) + ' €' : 'keine Daten' }} }}
    }},
    scales: {{
      y: {{ ticks: {{ callback: v => v + ' €' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""
    with open(DASHBOARD, "w", encoding="utf-8") as f:
        f.write(html)

# ─── Hauptprogramm ───────────────────────────────────────────────────────────

def run():
    print(f"\n{'='*55}")
    print(f"  ✈  Flugpreis-Crawler  |  {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*55}")

    # Hinflug NUE → PMI
    print("\n📡  Ryanair NUE → PMI ...")
    out_ryanair   = fetch_ryanair("NUE", "PMI", OUTBOUND_DATES)
    print(f"    → {len(out_ryanair)} Daten gefunden")

    print("📡  Eurowings NUE → PMI ...")
    out_eurowings = fetch_eurowings("NUE", "PMI", OUTBOUND_DATES)
    print(f"    → {len(out_eurowings)} Daten gefunden")

    print("📡  Condor NUE → PMI ...")
    out_condor    = fetch_condor("NUE", "PMI", OUTBOUND_DATES)
    print(f"    → {len(out_condor)} Daten gefunden")

    # Rückflug PMI → NUE
    print("\n📡  Ryanair PMI → NUE ...")
    ret_ryanair   = fetch_ryanair("PMI", "NUE", RETURN_DATES)
    print(f"    → {len(ret_ryanair)} Daten gefunden")

    print("📡  Eurowings PMI → NUE ...")
    ret_eurowings = fetch_eurowings("PMI", "NUE", RETURN_DATES)
    print(f"    → {len(ret_eurowings)} Daten gefunden")

    print("📡  Condor PMI → NUE ...")
    ret_condor    = fetch_condor("PMI", "NUE", RETURN_DATES)
    print(f"    → {len(ret_condor)} Daten gefunden")

    # Günstigste Preise je Datum
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

    priced  = sorted([c for c in combos if c["total"]], key=lambda x: x["total"])
    unpriced = [c for c in combos if not c["total"]]
    combos  = priced + unpriced

    best = priced[0] if priced else None
    today = datetime.now().strftime("%Y-%m-%d")

    # Verlaufsdaten laden und ergänzen
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

    print("\n" + "─"*55)
    print(f"✅  Daten gespeichert  →  {DATA_FILE.name}")
    print(f"✅  Dashboard erzeugt  →  {DASHBOARD.name}")
    if best:
        print(f"\n🏆  Bestes Angebot: {best['out_date']} → {best['ret_date']}  =  {best['total']:.2f} €")
        print(f"    ({best['out_airline']} hin · {best['ret_airline']} rück · {best['nights']} Nächte)")
    else:
        print("\n⚠   Keine Preise gefunden – APIs möglicherweise noch nicht verfügbar für diesen Zeitraum.")
    print("─"*55 + "\n")

if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("\n[FEHLER] Das Script ist abgestuerzt:")
        traceback.print_exc()
        sys.exit(1)
