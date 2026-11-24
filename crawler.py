#!/usr/bin/env python3
"""
Flugpreis-Crawler: NUE -> PMI / PMI -> NUE (nur Direktfluege, airlineunabhaengig)
Kombinationen werden automatisch aus den konfigurierten Reisezeitraeumen generiert.
"""

import base64
from datetime import datetime, date, timedelta
from html import escape, unescape
import json
import os
from pathlib import Path
import re
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

GOOGLE_HTML_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Standard-Cookie fuer abgelehnte Personalisierung (verhindert EU-Consent-Redirect)
GOOGLE_CONSENT_COOKIES = {
    "SOCS": "CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg",
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

    return f"{' & '.join(parts)} \u00b7 {nights_txt} \u00b7 Nur Direktfl\u00fcge"


COMBINATIONS   = build_combinations()
OUTBOUND_DATES = sorted(set(c["out"] for c in COMBINATIONS))
RETURN_DATES   = sorted(set(c["ret"] for c in COMBINATIONS))

# =============================================================================
#  Google Flights Protobuf-Encoder & Direktflug-Parser (alle Airlines)
# =============================================================================

MONTHS_EN = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

ARIA_NONSTOP_RE = re.compile(
    r'aria-label="(From [0-9,]+ euros\.[^"]*?Nonstop flight with [^"]*?Select flight)"'
)
PRICE_EUR_RE = re.compile(r"From ([0-9,]+) euros")
AIRLINE_RE   = re.compile(r"Nonstop flight with ([^.]+)\.")


def _pb_varint(n):
    out = bytearray()
    while n > 127:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _pb_field_varint(num, val):
    return _pb_varint((num << 3) | 0) + _pb_varint(val)


def _pb_field_bytes(num, data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _pb_varint((num << 3) | 2) + _pb_varint(len(data)) + data


def build_google_flights_tfs(legs, trip_type=2, nonstop_only=True):
    """
    Erzeugt den Base64-Protobuf-Parameter 'tfs' fuer Google Flights.
    legs: Liste aus Tupeln (dep_iata, arr_iata, 'YYYY-MM-DD')
    trip_type: 1 = Hin & Zurueck, 2 = Nur Hinflug
    """
    payload = _pb_field_varint(1, 28) + _pb_field_varint(2, trip_type)
    for dep, arr, date_str in legs:
        a_dep = _pb_field_varint(1, 1) + _pb_field_bytes(2, dep)
        a_arr = _pb_field_varint(1, 1) + _pb_field_bytes(2, arr)
        flight = _pb_field_bytes(2, date_str)
        if nonstop_only:
            flight += _pb_field_varint(5, 1)  # 1 = nur Direktfluege
        flight += _pb_field_bytes(13, a_dep) + _pb_field_bytes(14, a_arr)
        payload += _pb_field_bytes(3, flight)
    payload += _pb_field_varint(8, 1)   # 1 Erwachsener
    payload += _pb_field_varint(9, 1)   # Economy
    payload += _pb_field_varint(19, 2)  # Standard-Sortierung
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def parse_google_flights_nonstop(html_text, expected_date):
    """
    Extrahiert alle Direktfluege fuer das angefragte Datum aus dem Google-Flights-HTML.
    Prueft explizit auf 'Nonstop flight with ...' sowie das passende Abflugdatum.
    Gibt Liste von (price_float, airline_str) aufsteigend nach Preis zurueck.
    """
    dt = datetime.strptime(expected_date, "%Y-%m-%d")
    expected_day_fragment = f"{MONTHS_EN[dt.month]} {dt.day}"

    offers = []
    for m in ARIA_NONSTOP_RE.finditer(html_text):
        label = unescape(m.group(1))
        # Sicherstellen, dass es wirklich der angefragte Reisetag ist
        if expected_day_fragment not in label:
            continue
        mp = PRICE_EUR_RE.search(label)
        ma = AIRLINE_RE.search(label)
        if not mp or not ma:
            continue
        price = round(float(mp.group(1).replace(",", "")), 2)
        airline = ma.group(1).strip()
        if price > 0 and airline:
            offers.append((price, airline))

    offers.sort(key=lambda x: x[0])
    return offers


# =============================================================================
#  Flugpreis-Adapter
# =============================================================================

def _record_status(status, code_or_err):
    if status is not None and code_or_err is not None:
        status.setdefault("issues", set()).add(str(code_or_err))


def fetch_google_flights_nonstop(dep, arr, dates, status=None):
    """
    Fragt Google Flights fuer alle Airlines ab (gefiltert auf Direktfluege in EUR).
    Deckt u.a. Ryanair, Eurowings, Condor, Corendon, Marabu usw. ab.
    """
    req = ensure_requests()
    results = {}
    session = req.Session()

    for d in dates:
        try:
            tfs = build_google_flights_tfs([(dep, arr, d)], trip_type=2, nonstop_only=True)
            url = f"https://www.google.com/travel/flights/search?tfs={tfs}&hl=en&curr=EUR"
            r = session.get(
                url,
                headers=GOOGLE_HTML_HEADERS,
                cookies=GOOGLE_CONSENT_COOKIES,
                timeout=20,
            )
            if r.status_code != 200:
                print(f"  Google Flights {dep}->{arr} {d}: HTTP {r.status_code}")
                _record_status(status, f"HTTP {r.status_code}")
            elif "consent.google" in r.url:
                print(f"  Google Flights {dep}->{arr} {d}: Consent-Redirect")
                _record_status(status, "Consent-Redirect")
            elif "sorry/index" in r.url:
                print(f"  Google Flights {dep}->{arr} {d}: Rate-Limit")
                _record_status(status, "Rate-Limit")
            else:
                offers = parse_google_flights_nonstop(r.text, d)
                if offers:
                    best_price, best_airline = offers[0]
                    results[d] = {"price": best_price, "airline": best_airline}
                    if status is not None:
                        airlines_seen = status.setdefault("airlines", set())
                        for _, al in offers:
                            airlines_seen.add(al)
                    # Kurze Uebersicht der gefundenen Airlines pro Tag im Log
                    by_airline = {}
                    for p, al in offers:
                        if al not in by_airline or p < by_airline[al]:
                            by_airline[al] = p
                    summary_str = ", ".join(
                        f"{al} {p:.0f} EUR" for al, p in sorted(by_airline.items(), key=lambda x: x[1])
                    )
                    print(f"      {d}: {summary_str}")
                else:
                    print(f"      {d}: keine Direktfluege gefunden")
            time.sleep(0.8)
        except Exception as e:
            print(f"  Google Flights {dep}->{arr} {d}: {e}")
            _record_status(status, type(e).__name__)
    return results


def fetch_ryanair(dep, arr, dates, status=None):
    """
    Direkte Ryanair-FareFinder-API (centgenaue Direktflug-Preise als Ergaenzung & Fallback).
    """
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
    """Google-Flights-Suchlink direkt auf Hin-/Rueckflug NUE<->PMI (nur Direktfluege, EUR)."""
    tfs = build_google_flights_tfs(
        [("NUE", "PMI", out), ("PMI", "NUE", ret)],
        trip_type=1,
        nonstop_only=True,
    )
    return f"https://www.google.com/travel/flights/search?tfs={tfs}&hl=de&curr=EUR"

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
        airlines = info.get("airlines") or []
        if out_c or ret_c:
            extra = f"; Airlines: {escape(', '.join(airlines))}" if airlines else ""
            parts.append(f"{escape(name)} ({out_c}/{out_t} Hin, {ret_c}/{ret_t} R&uuml;ck{extra})")
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

    st_google  = {}
    st_ryanair = {}

    print("\n[1/4] Google Flights Direktfluege NUE -> PMI (alle Airlines) ...")
    out_google = fetch_google_flights_nonstop("NUE", "PMI", OUTBOUND_DATES, st_google)
    print(f"      -> {len(out_google)} Ergebnis(se)")

    print("[2/4] Ryanair API NUE -> PMI (centgenau / Fallback) ...")
    out_ryanair = fetch_ryanair("NUE", "PMI", OUTBOUND_DATES, st_ryanair)
    print(f"      -> {len(out_ryanair)} Ergebnis(se)")

    print("[3/4] Google Flights Direktfluege PMI -> NUE (alle Airlines) ...")
    ret_google = fetch_google_flights_nonstop("PMI", "NUE", RETURN_DATES, st_google)
    print(f"      -> {len(ret_google)} Ergebnis(se)")

    print("[4/4] Ryanair API PMI -> NUE (centgenau / Fallback) ...")
    ret_ryanair = fetch_ryanair("PMI", "NUE", RETURN_DATES, st_ryanair)
    print(f"      -> {len(ret_ryanair)} Ergebnis(se)")

    sources_summary = {
        "Google Flights Direktfl\u00fcge": {
            "out": len(out_google),
            "out_total": len(OUTBOUND_DATES),
            "ret": len(ret_google),
            "ret_total": len(RETURN_DATES),
            "airlines": sorted(st_google.get("airlines", set())),
            "issues": sorted(st_google.get("issues", set())),
        },
        "Ryanair API": {
            "out": len(out_ryanair),
            "out_total": len(OUTBOUND_DATES),
            "ret": len(ret_ryanair),
            "ret_total": len(RETURN_DATES),
            "issues": sorted(st_ryanair.get("issues", set())),
        },
    }

    # Guenstigster Direktflug-Preis je Datum aus allen Quellen
    # (Ryanair API zuerst fuer centgenaue Gleichstands-Aufloesung)
    outbound = merge_cheapest(out_ryanair, out_google)
    returns  = merge_cheapest(ret_ryanair, ret_google)

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
