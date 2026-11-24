#!/usr/bin/env python3
"""
Flugpreis-Crawler: NUE -> PMI / PMI -> NUE
Kombinationen werden automatisch aus den konfigurierten Reisezeitraeumen generiert.
"""

from datetime import datetime, date, timedelta
from html import escape
import json
import os
from pathlib import Path
import sys
import time
import traceback

try:
    import requests
except ImportError:
    requests = None

# =============================================================================
#  Konfiguration
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_FILE  = SCRIPT_DIR / "flight_data.json"
DASHBOARD  = SCRIPT_DIR / "index.html"

TRIP_ID    = "2027-05-mallorca"
TRIP_TITLE = "Mai/Juni 2027"

# Reisezeitraeume: fruehester Hinflug bis spaetester Rueckflug je Zeitraum
TRAVEL_WINDOWS = [
    {
        "label":      "Hauptzeitraum",
        "start":      date(2027, 5, 26),
        "end":        date(2027, 6, 1),
        "min_nights": 4,
        "max_nights": 4,
    },
    {
        "label":      "Alternative",
        "start":      date(2027, 5, 13),
        "end":        date(2027, 5, 17),
        "min_nights": 4,
        "max_nights": 4,
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


def ensure_requests():
    """Laedt requests bei Bedarf nach (nur im produktiven Lauf, nicht beim Import)."""
    global requests
    if requests is None:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
        import requests as req_mod
        requests = req_mod
    return requests


def atomic_write_text(path, content):
    """Schreibt Textdateien atomisch ueber eine temporaere Datei im selben Ordner."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, path)


# =============================================================================
#  Kombinationen automatisch generieren
# =============================================================================

def build_combinations(windows=None):
    """
    Generiert alle Hin/Rueck-Kombinationen ueber die konfigurierten
    Reisezeitraeume mit jeweils min_nights bis max_nights Naechten.
    """
    if windows is None:
        windows = TRAVEL_WINDOWS

    combos = []
    seen = set()
    for w in windows:
        start = w["start"]
        end = w["end"]
        min_n = w["min_nights"]
        max_n = w.get("max_nights")
        label = w.get("label", "")

        out = start
        while out <= end:
            ret = out + timedelta(days=min_n)
            while ret <= end:
                nights = (ret - out).days
                if max_n is None or nights <= max_n:
                    key = (out.strftime("%Y-%m-%d"), ret.strftime("%Y-%m-%d"))
                    if key not in seen:
                        seen.add(key)
                        combos.append({
                            "out":    key[0],
                            "ret":    key[1],
                            "nights": nights,
                            "window": label,
                        })
                ret += timedelta(days=1)
            out += timedelta(days=1)
    return combos


def format_window_summary(windows=None):
    """Erzeugt eine lesbare Beschreibung der konfigurierten Reisezeitraeume."""
    if windows is None:
        windows = TRAVEL_WINDOWS

    parts = []
    night_ranges = set()
    for w in windows:
        start = w["start"]
        end = w["end"]
        span = f"{start.strftime('%d.%m.')}\u2013{end.strftime('%d.%m.%Y')}"
        label = w.get("label", "")
        if label and label != "Hauptzeitraum":
            parts.append(f"{label} {span}")
        else:
            parts.append(span)
        night_ranges.add((w["min_nights"], w.get("max_nights")))

    if len(night_ranges) == 1:
        min_n, max_n = next(iter(night_ranges))
        if max_n == min_n:
            nights_txt = f"Jeweils {min_n} N\u00e4chte"
        elif max_n is None:
            nights_txt = f"Alle Kombinationen mit mindestens {min_n} N\u00e4chten"
        else:
            nights_txt = f"{min_n}\u2013{max_n} N\u00e4chte"
    else:
        nights_txt = "Alle konfigurierten Kombinationen"

    return f"{' & '.join(parts)} \u00b7 {nights_txt}"


COMBINATIONS   = build_combinations()
OUTBOUND_DATES = sorted(set(c["out"] for c in COMBINATIONS))
RETURN_DATES   = sorted(set(c["ret"] for c in COMBINATIONS))

# =============================================================================
#  Airline-APIs
# =============================================================================

def _record_status(status, code_or_err):
    if status is not None and code_or_err is not None:
        status.setdefault("issues", set()).add(str(code_or_err))


def fetch_ryanair(dep, arr, dates, status=None):
    req = ensure_requests()
    results = {}
    for d in dates:
        try:
            r = req.get(
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
                            results[fd] = {"price": round(float(fp), 2), "airline": "Ryanair"}
            else:
                print(f"  Ryanair {dep}->{arr} {d}: HTTP {r.status_code}")
                _record_status(status, f"HTTP {r.status_code}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Ryanair {dep}->{arr} {d}: {e}")
            _record_status(status, type(e).__name__)
    return results


def fetch_eurowings(dep, arr, dates, status=None):
    req = ensure_requests()
    results = {}
    session = req.Session()
    # Session-Cookies holen
    try:
        r0 = session.get(
            "https://www.eurowings.com/de.html",
            headers=HEADERS,
            timeout=10,
        )
        if r0.status_code != 200:
            _record_status(status, f"HTTP {r0.status_code}")
    except Exception as e:
        _record_status(status, type(e).__name__)

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
                    if fd and fp and float(fp) > 0:
                        if fd not in results or float(fp) < results[fd]["price"]:
                            results[fd] = {"price": round(float(fp), 2), "airline": "Eurowings"}
            else:
                print(f"  Eurowings {dep}->{arr} {d}: HTTP {r.status_code}")
                _record_status(status, f"HTTP {r.status_code}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Eurowings {dep}->{arr} {d}: {e}")
            _record_status(status, type(e).__name__)

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
                else:
                    print(f"  Eurowings v2 {dep}->{arr} {d}: HTTP {r2.status_code}")
                    _record_status(status, f"HTTP {r2.status_code}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Eurowings v2 {dep}->{arr} {d}: {e}")
                _record_status(status, type(e).__name__)
    return results


def fetch_condor(dep, arr, dates, status=None):
    req = ensure_requests()
    results = {}
    for d in dates:
        # Versuch 1: REST-API
        try:
            r = req.get(
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
            else:
                print(f"  Condor {dep}->{arr} {d}: HTTP {r.status_code}")
                _record_status(status, f"HTTP {r.status_code}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Condor {dep}->{arr} {d}: {e}")
            _record_status(status, type(e).__name__)
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
#  Verlauf & Preistrend
# =============================================================================

def get_trip_dates(history, trip_id=TRIP_ID):
    """Gibt sortierte Datums-Schluessel der Historie fuer den aktuellen Trip zurueck."""
    if trip_id is None:
        return sorted(history.keys())
    return sorted(k for k, v in history.items() if v.get("trip") == trip_id)


def get_trends(history, today, trip_id=TRIP_ID):
    """
    Vergleicht heutige Preise mit dem letzten vorhandenen Tag desselben Trips.
    Gibt { (out_date, ret_date): {"trend": "up"|"down"|"same"|None, "diff": float} } zurueck.
    """
    trip_days = get_trip_dates(history, trip_id=trip_id)
    prev_days = [k for k in trip_days if k < today]
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

def format_sources_footer(sources):
    """Formatiert den Quellenstatus transparent fuer die Fusszeile."""
    if not sources:
        return ""
    parts = []
    for name, info in sources.items():
        out_c = info.get("out", 0)
        ret_c = info.get("ret", 0)
        out_t = info.get("out_total", 0)
        ret_t = info.get("ret_total", 0)
        issues = info.get("issues") or []
        if out_c or ret_c:
            parts.append(f"{escape(name)} ({out_c}/{out_t} Hin, {ret_c}/{ret_t} R&uuml;ck)")
        elif issues:
            parts.append(f"{escape(name)} (0 &ndash; {escape(', '.join(issues))})")
        else:
            parts.append(f"{escape(name)} (0)")
    return f"<br>Quellenstatus: {' &middot; '.join(parts)}"

def generate_dashboard(history, today):
    today_data = history.get(today, {})
    trip_id    = today_data.get("trip", TRIP_ID)
    combos     = today_data.get("combos", [])
    best       = today_data.get("best")
    sources    = today_data.get("sources")
    ts         = today_data.get("timestamp", "")
    ts_display = datetime.fromisoformat(ts).strftime("%d.%m.%Y um %H:%M Uhr") if ts else "-"
    trends     = get_trends(history, today, trip_id=trip_id)

    hist_dates   = get_trip_dates(history, trip_id=trip_id)[-30:]
    chart_labels = json.dumps(hist_dates)
    chart_values = json.dumps([
        history[d]["best"]["total"] if history[d].get("best") else None
        for d in hist_dates
    ])

    rows = ""
    for c in combos:
        is_best = best and c["out_date"] == best["out_date"] and c["ret_date"] == best["ret_date"]
        row_cls = ' class="best-row"' if is_best else ""
        badges  = []
        if is_best:
            badges.append('<span class="badge">Bestes Angebot</span>')
        if c.get("window") == "Alternative":
            badges.append('<span class="badge-alt">Alternative</span>')
        badge_html = ("<br>" + " ".join(badges)) if badges else ""
        t_info  = trends.get((c["out_date"], c["ret_date"]))

        out_p  = (f'{c["out_price"]:.2f} &euro;<br><small>{escape(str(c["out_airline"]))}</small>'
                  if c["out_price"] else '<span class="na">-</span>')
        ret_p  = (f'{c["ret_price"]:.2f} &euro;<br><small>{escape(str(c["ret_airline"]))}</small>'
                  if c["ret_price"] else '<span class="na">-</span>')
        total  = (f'<strong>{c["total"]:.2f} &euro;</strong> {trend_badge(t_info)}'
                  if c["total"] else '<span class="na">keine Daten</span>')

        rows += f"""
        <tr{row_cls}>
          <td>{fmt_date(c["out_date"])}{badge_html}</td>
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
        best_win = f" &nbsp;&middot;&nbsp; {escape(str(best['window']))}" if best.get("window") == "Alternative" else ""
        best_card = f"""
  <div class="best-card">
    <div class="best-label">G&uuml;nstigstes Angebot heute</div>
    <div class="best-price">{best["total"]:.2f} &euro; {trend_badge(t_best)}</div>
    <div class="best-details">
      {fmt_date(best["out_date"])} &rarr; {fmt_date(best["ret_date"])}
      &nbsp;&middot;&nbsp; {best["nights"]} N&auml;chte{best_win}
      &nbsp;&middot;&nbsp; Hin: {escape(str(best["out_airline"]))}
      &nbsp;&middot;&nbsp; R&uuml;ck: {escape(str(best["ret_airline"]))}
    </div>
  </div>"""

    subtitle_html = escape(format_window_summary())
    sources_html  = format_sources_footer(sources)

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flugpreise NUE &rarr; PMI | {escape(TRIP_TITLE)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f4f8; color: #1a202c; }}
    .header {{ background: linear-gradient(135deg, #1a365d, #2b6cb0);
               color: white; padding: 32px 40px; }}
    .header h1 {{ font-size: 26px; font-weight: 700; }}
    .header .sub {{ opacity: .85; margin-top: 6px; font-size: 14px; }}
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
    .badge-alt {{ background: #edf2f7; color: #4a5568; font-size: 10px; font-weight: 600;
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
    .footer {{ text-align: center; color: #718096; font-size: 12px;
               margin-top: 28px; padding-bottom: 8px; line-height: 1.6; }}
  </style>
</head>
<body>
<div class="header">
  <h1>Flugpreise N&uuml;rnberg (NUE) &rarr; Mallorca (PMI)</h1>
  <div class="sub">{subtitle_html}</div>
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
    Preise ohne Gew&auml;hr &middot; Direkt beim Anbieter verifizieren &middot; Automatisch generiert{sources_html}
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

    atomic_write_text(DASHBOARD, html)

# =============================================================================
#  Hauptprogramm
# =============================================================================

def run():
    # UTF-8 Ausgabe sicherstellen (wichtig fuer GitHub Actions / Linux)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    ensure_requests()

    print(f"\n{'='*55}")
    print(f"  Flugpreis-Crawler  |  {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"  Trip: {TRIP_ID} | {format_window_summary()}")
    print(f"  Kombinationen: {len(COMBINATIONS)} | Hinflugdaten: {OUTBOUND_DATES} | Rueckflugdaten: {RETURN_DATES}")
    print(f"{'='*55}")

    st_ryanair   = {}
    st_eurowings = {}
    st_condor    = {}

    print("\n[1/6] Ryanair NUE -> PMI ...")
    out_ryanair   = fetch_ryanair("NUE", "PMI", OUTBOUND_DATES, st_ryanair)
    print(f"      -> {len(out_ryanair)} Ergebnis(se)")

    print("[2/6] Eurowings NUE -> PMI ...")
    out_eurowings = fetch_eurowings("NUE", "PMI", OUTBOUND_DATES, st_eurowings)
    print(f"      -> {len(out_eurowings)} Ergebnis(se)")

    print("[3/6] Condor NUE -> PMI ...")
    out_condor    = fetch_condor("NUE", "PMI", OUTBOUND_DATES, st_condor)
    print(f"      -> {len(out_condor)} Ergebnis(se)")

    print("[4/6] Ryanair PMI -> NUE ...")
    ret_ryanair   = fetch_ryanair("PMI", "NUE", RETURN_DATES, st_ryanair)
    print(f"      -> {len(ret_ryanair)} Ergebnis(se)")

    print("[5/6] Eurowings PMI -> NUE ...")
    ret_eurowings = fetch_eurowings("PMI", "NUE", RETURN_DATES, st_eurowings)
    print(f"      -> {len(ret_eurowings)} Ergebnis(se)")

    print("[6/6] Condor PMI -> NUE ...")
    ret_condor    = fetch_condor("PMI", "NUE", RETURN_DATES, st_condor)
    print(f"      -> {len(ret_condor)} Ergebnis(se)")

    sources_summary = {
        "Ryanair": {
            "out": len(out_ryanair),
            "out_total": len(OUTBOUND_DATES),
            "ret": len(ret_ryanair),
            "ret_total": len(RETURN_DATES),
            "issues": sorted(st_ryanair.get("issues", set())),
        },
        "Eurowings": {
            "out": len(out_eurowings),
            "out_total": len(OUTBOUND_DATES),
            "ret": len(ret_eurowings),
            "ret_total": len(RETURN_DATES),
            "issues": sorted(st_eurowings.get("issues", set())),
        },
        "Condor": {
            "out": len(out_condor),
            "out_total": len(OUTBOUND_DATES),
            "ret": len(ret_condor),
            "ret_total": len(RETURN_DATES),
            "issues": sorted(st_condor.get("issues", set())),
        },
    }

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
            "window":      c.get("window", ""),
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

    # Verlaufsdaten laden & aktualisieren (historische Trips bleiben erhalten)
    history = {}
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            history = json.load(f)

    history[today] = {
        "trip":      TRIP_ID,
        "combos":    combos,
        "best":      best,
        "sources":   sources_summary,
        "timestamp": datetime.now().isoformat(),
    }

    atomic_write_text(DATA_FILE, json.dumps(history, indent=2, ensure_ascii=False))
    generate_dashboard(history, today)

    print(f"\n{'='*55}")
    print(f"  Daten gespeichert  ->  {DATA_FILE.name}")
    print(f"  Dashboard erzeugt  ->  {DASHBOARD.name}")
    if best:
        win_info = f" [{best['window']}]" if best.get("window") else ""
        print(f"\n  Bestes Angebot: {best['out_date']} -> {best['ret_date']}{win_info}"
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
