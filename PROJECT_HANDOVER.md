# Projektübergabe: Flugpreis-Tracker Nürnberg – Mallorca

> **Stand: 14. November 2026, Europe/Berlin.** Diese Datei dokumentiert das tatsächlich in VS Code geöffnete Git-Repository `flugcrawler` auf dem NAS. Sie beschreibt den bestehenden Code und die zugängliche Projektgeschichte; sie ist kein Auftrag, den derzeit nicht benötigten Tracker wieder zu aktivieren.

## 0. Orientierung, Quellenlage und belastbarer Ausgangsstand

### 0.1 In einer Minute verstehen

Das Projekt ist ein kleiner Python-Batchprozess für Flugpreise zwischen Nürnberg (`NUE`) und Palma de Mallorca (`PMI`). Er ermittelt zulässige Hin-/Rückflug-Kombinationen in einem festen Reisefenster, fragt mehrere Quellen an, addiert die jeweils günstigsten gefundenen Einzelflüge und erzeugt eine statische HTML-Tabelle mit Preisverlauf. GitHub Actions übernimmt die zeitgesteuerte Ausführung; GitHub Pages wurde zur Veröffentlichung des Dashboards verwendet.

Die rechnerische Auswertung und die HTML-Erstellung funktionieren mit den gespeicherten Daten. **Die gewünschte airlineübergreifende Marktabdeckung ist jedoch nicht erreicht: In der gesamten vorhandenen Preisgeschichte finden sich ausschließlich Ryanair-Preise.** Die Eurowings- und Condor-Adapter sind Versuche mit im früheren Chat ausdrücklich als geraten eingeräumten Endpunkten.

Der letzte bekannte Betriebswunsch des Nutzers lautet: **Automatische Abfragen und öffentliche Webseite vorerst abschalten, Code für eine spätere Nutzung behalten.** Das Repository ist laut in dieser Sitzung abgefragten GitHub-Metadaten privat. Ob Workflow und Pages tatsächlich deaktiviert sind, wurde nicht abschließend geprüft. Keinen Workflow zum Testen starten und keine Seite veröffentlichen, solange kein neuer Auftrag dazu vorliegt.

### 0.2 Herkunft von Aussagen

| Kennzeichnung | Bedeutung |
| --- | --- |
| **Code / Git / Daten** | Durch aktuelle Dateien, lokale Versionsgeschichte oder gespeicherte JSON-Daten verifiziert. |
| **Remote-Beobachtung** | In dieser Unterhaltung über die verbundene GitHub-Schnittstelle gelesene Repository-Metadaten, Laufdaten oder Logs. |
| **Gespräch** | Anforderung, Rückmeldung oder Entscheidung aus dem tatsächlich sichtbaren Gesprächsverlauf. Eine frühere Erfolgsmeldung eines Assistenten ist allein kein Funktionsnachweis. |
| **Ableitung / offen** | Technische Schlussfolgerung oder nicht verifizierter Sachverhalt. Keine zugesicherte Funktion und kein automatisch erteilter Entwicklungsauftrag. |

Zugänglich war der lange Verlauf dieses Threads: ursprünglicher Bau in Cowork, lokale Einrichtung, Umstieg auf GitHub, Erweiterungswünsche, Datenquellenprobleme, Stilllegungswunsch sowie die anschließende lokale Synchronisierung. **Andere Chats, private Notizen und möglicherweise frühere Unterhaltungen außerhalb dieses Threads sind nicht zugänglich.** Auch historische Tool-Ausgaben und damalige erzeugte Dateien sind teilweise nur als Auszüge sichtbar. Es wird daher keine lückenlose Kenntnis sämtlicher früheren Chats behauptet.

### 0.3 Versions- und Datenstand

| Gegenstand | Verifizierter Stand |
| --- | --- |
| Repository | `Moritz2011/flugcrawler` |
| Standardbranch / lokaler Branch | `main` |
| Lokaler HEAD und zuletzt abgerufener `origin/main` | `58f9bce5da793d645222ee982b8a5fb30c2bbbe1` |
| Letzter Commit | Preisupdate vom 09.10.2026, 12:09:37 UTC |
| Letzte Änderung an `crawler.py` | `3bd5a6118303f22280d4465bd89b0a3e2b98a9ff`, 30.04.2026 |
| Erster Implementierungscommit | `ada0d31fecba580da94c2241c981670ec07bffa9`, 29.04.2026 |
| Git-Status vor Erstellung dieser Datei | `working tree clean`; gegenüber `origin/main` weder voraus noch zurück |
| Verfolgte Projektdateien vor dieser Dokumentation | 6; siehe Abschnitt B |
| Historie | 164 Tagesstände vom 29.04.2026 bis 09.10.2026, insgesamt 983 Kombinationseinträge |
| Airlines in sämtlichen gespeicherten Kombinationen | ausschließlich `Ryanair` |
| Reisefenster im Code | 22.10.2026 bis einschließlich 26.10.2026, mindestens 2 Nächte |
| Wichtig zum heutigen Datum | Das konfigurierte Reisefenster liegt inzwischen in der Vergangenheit. |

Diese Datei wurde zunächst als Entwurf unversioniert angelegt und auf ausdrücklichen Wunsch des Nutzers am 14. November 2026 ins Git-Repository aufgenommen und gepusht, um dauerhaft als zentrale Wissensbasis erhalten zu bleiben.

## A. Projektübersicht und Zielsetzung

### A.1 Zweck und Zielgruppe

Der Nutzer wollte für mehrere mögliche Reisetermine nicht täglich selbst auf Flugwebseiten suchen. Gewünscht war eine automatisch aktualisierte, jederzeit aufrufbare HTML-Seite mit einer übersichtlichen Tabelle und der günstigsten zulässigen Kombination.

Zielgruppe ist zunächst der einzelne Nutzer. Mehrbenutzerbetrieb, Reisebuchung, Zahlungsabwicklung oder eine kommerzielle Reiseplattform gehören nicht zum dokumentierten Auftrag.

### A.2 Funktionale Zielsetzung

Aus dem Gespräch ergeben sich folgende verbindliche beziehungsweise bereits akzeptierte Ziele:

- Strecke Nürnberg – Mallorca und zurück.
- Die Airline ist egal; entscheidend ist der günstigste Hin-/Rückflug-Gesamtpreis unter den zulässigen Kombinationen.
- Mindestens zwei Nächte Aufenthalt.
- Zuletzt vereinbartes statisches Reisefenster: Donnerstag, 22.10.2026, bis Montag, 26.10.2026.
- Automatische tägliche Ausführung; alle zwei Tage wurde anfangs als Alternative besprochen, gewählt wurde täglich.
- Ausführung unabhängig davon, ob der Mac eingeschaltet ist.
- HTML-Dashboard mit Tabelle, hervorgehobener günstigster Kombination, Aktualisierungszeit und historischem Preisverlauf.
- Preistrend mit grünem Abwärts-, rotem Aufwärts- und grauem Gleichbleibend-Indikator.
- Datumsbereich im Code pflegen; eine interaktive Datumsverwaltung war nicht gewünscht.

Ursprünglich war der Hinflug auf den 22. oder 23. Oktober beschränkt. Später wurde ausdrücklich das gesamte Fenster 22.–26. Oktober mit mindestens zwei Nächten gewünscht. **Die spätere Anforderung gilt:** Damit ist auch 24.10. → 26.10. zulässig.

### A.3 Aktueller Entwicklungs- und Betriebsstand

Es existiert ein funktionierender kleiner Batchprozess mit Datenspeicherung und statischem Dashboard. Der Nutzer bestätigte zuvor einen grünen Actions-Lauf und eine erreichbare Pages-Seite sowie die erfolgreiche Übernahme der Erweiterungen.

Das wichtigste fachliche Defizit ist weiterhin die unvollständige Preisabdeckung. Ein Ergebnis ist der günstigste **von den funktionierenden Quellen gelieferte** Preis, keine nachgewiesene Bestpreisermittlung über alle Airlines und Buchungsportale.

Aktuell steht die Aufbewahrung des Codes im Vordergrund. Ein Wiederanlauf, neue Reisedaten oder der Wechsel auf einen Datenanbieter sind nicht beauftragt. Die Entwicklung soll später auch von einem anderen KI-Coding-Assistenten, insbesondere Google Antigravity, fortgesetzt werden können.

Ein darüber hinausgehendes langfristiges Produktziel wurde nicht vereinbart.

## B. Technische Architektur

### B.1 Projektstruktur

Alle folgenden Dateipfade beziehen sich auf den Stamm des tatsächlichen Git-Repositories:

```text
flugcrawler/
├── .github/
│   └── workflows/
│       └── crawler.yml       # Actions-Zeitplan, Laufzeit und Ergebnis-Commit
├── .gitignore                # Ausschluss alter lokaler Setup-/Demodateien
├── crawler.py                # Gesamte Python-Anwendungslogik und HTML-Template
├── flight_data.json          # Persistente tägliche Preisgeschichte
├── index.html                # Zuletzt generiertes Dashboard
├── requirements.txt          # Python-Abhängigkeit requests, ohne Versionsbindung
└── PROJECT_HANDOVER.md       # Zentrale Wissensbasis und Übergabedokumentation
```

Zusätzlich sind lokal vorhandene, ignorierte Dateien bekannt:

- `dashboard_preview.html`: alte Vorschau mit ausdrücklich gekennzeichneten Beispieldaten.
- `flight_data_demo.json`: alte synthetische Verlaufsdaten.
- `.vscode/extensions.json`: leere Liste von Erweiterungsempfehlungen; keine Laufzeitfunktion.
- `.DS_Store`: Finder-Metadaten; für das Projekt ohne Bedeutung.

Diese Dateien sind keine produktiven Datenquellen. In der Vorschau gezeigte Eurowings-Preise sind **kein** Nachweis für einen funktionierenden Eurowings-Adapter.

Im untersuchten Projekt gibt es keine `README`, keine vorhandene `AGENTS.md`, keine weiteren projektspezifischen Entwicklungsanweisungen, keine Testdateien und keine Lizenzdatei. Aus der früheren Erwähnung von `setup.sh` folgt nicht, dass diese Datei heute vorhanden oder funktionsfähig ist; sie wird zwar ignoriert, ist im aktuellen untersuchten Bestand aber nicht vorhanden.

### B.2 Technologien

| Ebene | Tatsächliche Umsetzung |
| --- | --- |
| Verarbeitung | Ein Python-Skript, `crawler.py`, 548 Zeilen im dokumentierten Commit |
| CI-Laufzeit | Python 3.11 über `actions/setup-python@v5`, Runner `ubuntu-latest` |
| HTTP | `requests`; teilweise `requests.Session()` für Eurowings-Cookies |
| Standardbibliothek | `json`, `sys`, `time`, `traceback`, `datetime`, `pathlib`; `subprocess` im Installationsfallback |
| Frontend | Statisches HTML, eingebettetes CSS und JavaScript, durch Python-F-String erzeugt |
| Diagramm | Chart.js 4.4.0 über jsDelivr-CDN |
| Datenhaltung | Eine JSON-Datei im Repository; keine SQL-/NoSQL-Datenbank |
| Automatisierung | `.github/workflows/crawler.yml` mit `schedule` und `workflow_dispatch` |
| Hosting | Historisch GitHub Pages aus Branch `main`, Verzeichnis `/ (root)` |
| Versionsverwaltung | Git; aktueller lokaler Zugang zu GitHub über SSH |

Kein Webframework, kein dauerhaft laufendes Backend, kein Node-/npm-Projekt, kein Docker-Setup, kein Browser-Automatisierungsframework und kein Paket-Build sind implementiert.

### B.3 Komponenten und Datenfluss

```text
Actions-Zeitplan oder manuelle Auslösung
    → Repository auschecken
    → Python einrichten und requests installieren
    → crawler.py starten
        → Datums-Kombinationen aus Konstanten ermitteln
        → je Richtung Ryanair, Eurowings und Condor abfragen
        → je Datum den günstigsten gelieferten Einzelflug auswählen
        → Hin- und Rückpreise addieren und Kombinationen sortieren
        → vorhandene flight_data.json lesen
        → heutigen Tagesstand einsetzen / überschreiben
        → flight_data.json schreiben
        → Trends und Chartdaten berechnen
        → index.html schreiben
    → flight_data.json und index.html committen und pushen

Gesonderte Pages-Veröffentlichung
    → statische index.html über Website-URL ausliefern
    → Browser lädt zusätzlich Chart.js vom CDN
```

Der Browser fragt selbst keine Airline-Preise ab. Die dargestellten Preise und Diagrammdaten sind in die HTML-Datei eingebettet. `index.html` lädt `flight_data.json` nicht zur Laufzeit nach.

Die Generierungslogik liegt in `crawler.py`, nicht in Pages. Änderungen nur an der generierten `index.html` werden beim nächsten Lauf überschrieben.

### B.4 Wichtige Funktionen und Einstiegspunkte

Zeilenangaben beziehen sich auf Commit `58f9bce` und können sich später verschieben. Funktionsnamen sind die dauerhafteren Referenzen.

| Stelle in `crawler.py` | Verantwortung |
| --- | --- |
| Zeilen 14–25 | UTF-8-Ausgabe und automatischer `requests`-Installationsfallback beim Import |
| Zeilen 31–47 | Ausgabepfade, Reisefenster, Mindestnächte und HTTP-Header |
| `build_combinations()`, Zeile 53 | Alle zulässigen Kalenderdatumspaare erzeugen |
| `COMBINATIONS`, `OUTBOUND_DATES`, `RETURN_DATES`, Zeilen 72–74 | Beim Modulimport berechnete Suchparameter |
| `fetch_ryanair()`, Zeile 80 | FareFinder-Abfragen und tägliche Minimalpreise |
| `fetch_eurowings()`, Zeile 109 | Session-Aufruf, primärer Adapter und zweiter Versuch |
| `fetch_condor()`, Zeile 180 | Versuchsadapter für Condor |
| `merge_cheapest()`, Zeile 211 | Pro Datum den niedrigsten Quellenpreis behalten |
| `get_trends()`, Zeile 224 | Kombination mit dem letzten gespeicherten früheren Tag vergleichen |
| `fmt_date()`, Zeile 258 | Deutsche Wochentage und Datumsausgabe |
| `gf_url()`, Zeile 264 | Google-Flights-Suchlink für Route und Reisedaten |
| `trend_badge()`, Zeile 270 | HTML für Preisänderungsindikatoren |
| `generate_dashboard()`, Zeile 281 | Vollständiges HTML samt CSS und Chart-Konfiguration erstellen |
| `run()`, Zeile 455 | Abfragen, Zusammenführen, Speicherung und HTML-Erzeugung orchestrieren |
| `if __name__ == "__main__"`, Zeile 542 | Programmstart; unbehandelte Fehler mit Traceback und Exitcode 1 |

### B.5 Konfiguration und Suchsemantik

Die aktuelle Konfiguration ist im Quellcode festgelegt:

```python
TRAVEL_START = date(2026, 10, 22)
TRAVEL_END   = date(2026, 10, 26)
MIN_NIGHTS   = 2
```

`TRAVEL_START` ist der früheste Hinflugtag, `TRAVEL_END` der späteste Rückflugtag. Für jeden Hinflug werden alle Rückflüge ab `Hinflug + MIN_NIGHTS` bis zum Ende des Fensters erzeugt. Nächte sind eine Differenz von Kalenderdaten; Flugzeiten oder tatsächlich am Ziel verbrachte Stunden werden nicht ausgewertet.

| Hinflug | Rückflug | Nächte |
| --- | --- | --- |
| 22.10.2026 | 24.10.2026 | 2 |
| 22.10.2026 | 25.10.2026 | 3 |
| 22.10.2026 | 26.10.2026 | 4 |
| 23.10.2026 | 25.10.2026 | 2 |
| 23.10.2026 | 26.10.2026 | 3 |
| 24.10.2026 | 26.10.2026 | 2 |

Es werden drei unterschiedliche Hinflugtage und drei unterschiedliche Rückflugtage abgefragt. Die Anfragen werden je Datum wiederverwendet, statt jede Kombination separat vollständig abzufragen.

Weitere Einstellungen:

- Strecke `NUE` / `PMI` ist mehrfach fest in `run()`, `gf_url()` und im HTML-Text hinterlegt.
- Währung `EUR` ist in den Adapterparametern und der Darstellung fest eingebaut.
- Eurowings-Fallback und Condor übergeben `adults=1`; Eurowings primär `passengerTypes=ADULT`. Ryanair nutzt den FareFinder ohne explizite Reisendenzahl. Das Dashboard bezeichnet Preise als „p.P.“.
- Gepäck, Sitzplätze, Tarifbedingungen, Zahlungsgebühren, Flugnummern, Tageszeiten und Umstiege sind keine modellierten Auswahlkriterien.
- Titel und Untertitel enthalten weiterhin hart codiert „Oktober 2026“. Das Ändern allein der Datumskonstanten aktualisiert diese Texte nicht.

Konstanten werden beim Import ausgewertet. Wer in Tests oder späterer Laufzeit nur `TRAVEL_START` ändert, muss abhängige Kombinationen ebenfalls neu berechnen.

### B.6 Datenmodelle

Ein Adapter liefert das vereinheitlichte interne Format:

```json
{
  "2026-10-22": {
    "price": 14.99,
    "airline": "Ryanair"
  }
}
```

`merge_cheapest()` arbeitet ausschließlich mit Datum, `price` und `airline`. Bei Preisgleichheit bleibt das zuerst übergebene Ergebnis erhalten. Derzeit ist die Aufrufreihenfolge Ryanair, Eurowings, Condor.

`flight_data.json` ist ein Objekt mit Tagesdatum als Schlüssel. Ein tatsächliches, gekürztes Schema-Beispiel aus dem gespeicherten Stand:

```json
{
  "2026-10-09": {
    "combos": [
      {
        "out_date": "2026-10-22",
        "ret_date": "2026-10-26",
        "nights": 4,
        "out_price": 14.99,
        "out_airline": "Ryanair",
        "ret_price": 159.7,
        "ret_airline": "Ryanair",
        "total": 174.69
      }
    ],
    "best": {
      "out_date": "2026-10-22",
      "ret_date": "2026-10-26",
      "nights": 4,
      "out_price": 14.99,
      "out_airline": "Ryanair",
      "ret_price": 159.7,
      "ret_airline": "Ryanair",
      "total": 174.69
    },
    "timestamp": "2026-10-09T12:09:37.714568"
  }
}
```

Das Beispiel zeigt nur eine der sechs Kombinationen dieses Tages. Es sind historische Daten, kein aktuelles Angebot.

Wichtige Vertragsdetails:

- Fehlender Hin-/Rückpreis und zugehörige Airline werden als `null` gespeichert.
- `total` ist nur vorhanden, wenn beide Richtungen einen Preis geliefert haben; sonst `null`.
- Vollständige Kombinationen werden aufsteigend nach Gesamtpreis sortiert; unvollständige folgen danach.
- `best` enthält die günstigste vollständige Kombination oder `null`.
- Preise werden als Python-`float` verarbeitet und auf zwei Nachkommastellen gerundet.
- Pro Ausführung wird `history[today]` neu eingesetzt. Mehrere Läufe am selben Datum überschreiben diesen Tagesstand; es gibt keine Intraday-Historie.
- `timestamp` enthält keine Zeitzonenangabe. Auch der Tages-Schlüssel verwendet die lokale Zeitzone der ausführenden Maschine.
- Die gesamte Historie bleibt in der Datei; nur die Diagrammdarstellung beschränkt sich auf die letzten 30 vorhandenen Tages-Schlüssel.
- Keine Schema-Version, keine Suchkonfigurations-ID, keine vollständigen Rohangebote und keine Quellenstatusdaten werden gespeichert.

### B.7 Externe Schnittstellen

Die folgende Tabelle dokumentiert **den bestehenden Code**, keine zugesicherte öffentliche API-Verfügbarkeit:

| Quelle | Im Code verwendete URL / Antwortannahme | Belegter Zustand |
| --- | --- | --- |
| Ryanair | `https://www.ryanair.com/api/farfnd/v4/oneWayFares`; liest `fares[].outbound.departureDate` und `fares[].outbound.price.value` | Historisch erfolgreich, im letzten geprüften Lauf drei Datumsergebnisse je Richtung. Keine aktuelle Erreichbarkeitsprüfung für neue Flüge durchgeführt. |
| Eurowings, primär | `https://www.eurowings.com/api/ndsservices/shoppingbasket/v1.0.0/flightoffers/cheapestfares`; erwartet `flightOffers[]`, `departureDate`, `price.amount` | Geratener beziehungsweise nicht validierter Adapter; im letzten geprüften Lauf kein Ergebnis. |
| Eurowings, Fallback | `https://www.eurowings.com/api/v2/flightsearch/availability`; versucht `lowestFare`, `cheapestFare` oder ersten `fares[].totalPrice` | Ebenfalls nicht durch erfolgreiche reale Ergebnisse nachgewiesen. |
| Condor | `https://www.condor.com/de/flugangebote/api/v1/flights`; versucht `flights` oder `offers`, Datum und `price.amount` oder `totalPrice` | Geratener beziehungsweise nicht validierter Adapter; im letzten geprüften Lauf kein Ergebnis. |
| Eurowings-Startseite | `https://www.eurowings.com/de.html` | Session-Cookies vor den Preisabfragen; kein eigener Preislieferant. |
| Google Flights | Von `gf_url()` erzeugter Suchlink mit URL-Fragment für Hin-/Rückdaten | Nur Navigation bei Klick auf „Suchen“; keine Abfrage oder Preisgewinnung durch den Crawler. Aktuelle Linkfunktion nicht im Browser getestet. |
| jsDelivr | `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js` | JavaScript-Bibliothek für das Diagramm im Browser, nicht für die Preisermittlung. |

HTTP-Anfragen laufen synchron. Preisaufrufe verwenden `timeout=15`; der Eurowings-Startseitenaufruf `timeout=10`. Im Normalpfad wird nach einem Versuch 0,5 Sekunden gewartet. Es gibt keine eigene Wiederholungsstrategie, keine Parallelisierung und keine dokumentierte SLA.

Alle Adapter akzeptieren nur HTTP 200 zur Auswertung. Andere Statuscodes werden nicht ausdrücklich protokolliert. Exceptions werden je Adapterversuch abgefangen und als kurze Meldung ausgegeben. Dadurch wird eine fehlgeschlagene Quelle nicht automatisch zum fehlgeschlagenen Gesamtjob.

### B.8 Automatisierung und Hosting

`.github/workflows/crawler.yml` enthält:

```yaml
on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: write
```

Die Schritte sind `actions/checkout@v4`, `actions/setup-python@v5` mit Python 3.11, `pip install -r requirements.txt`, `python crawler.py` und schließlich Commit/Push der beiden Ergebnisdateien. Für den Python-Schritt werden `PYTHONIOENCODING=utf-8` und `PYTHONUNBUFFERED=1` gesetzt.

Der Workflow wird in `.github/workflows/` erkannt. Sein Dateiname ist frei wählbar, der Verzeichnispfad ist Teil der GitHub-Konvention. Es gibt keine separate Scheduler-Implementierung in Python.

**Zeitplan-Korrektur:** `0 6 * * *` ist in dieser Konfiguration ein fester UTC-Zeitplan: im deutschen Sommer 08:00, im Winter 07:00. Die Kommentare im YAML behaupten zu weitgehend, CET/CEST sei berücksichtigt. Auch Oktober ist nicht durchgehend Sommerzeit. Geplante GitHub-Läufe können verspätet starten; „exakt jeden Morgen um 08:00“ ist daher nicht zugesichert.

Pages ist separat konfiguriertes Hosting. Historisch wurde `main` und `/ (root)` ausgewählt; deshalb liegt `index.html` im Repository-Stamm. Diese Website wurde zuvor unter `https://moritz2011.github.io/flugcrawler/` aufgerufen. Die heutige Erreichbarkeit wird hier nicht zugesichert.

**Wichtige Deployment-Einschränkung:** Der Crawler-Workflow enthält keinen expliziten Pages-Artefakt-Upload und keinen `deploy-pages`-Schritt. Laut [GitHub-Dokumentation zur Publishing-Quelle](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) lösen mit `GITHUB_TOKEN` gepushte Commits keinen Pages-Build aus. Gleichzeitig ist im hier eingesehenen Verlauf am 09.10.2026 ein erfolgreicher separater Pages-Lauf zum Ergebniscommit vorhanden. Diese beobachtete Veröffentlichung belegt keinen allgemeinen Automatismus; der genaue Auslösemechanismus wurde nicht geklärt. Bei späterer Reaktivierung die gesamte Kette bis zum sichtbaren Website-Inhalt prüfen.

### B.9 Authentifizierung, Benutzer und Secrets

- Die Anwendung hat keine Benutzerkonten und keinen Login.
- Die vorhandenen Airline-Adapter verwenden keine API-Schlüssel, sondern normale HTTP-Aufrufe mit festen Headern und ggf. Session-Cookies.
- Für Actions-Checkout und Push ist GitHub-Authentifizierung erforderlich; `contents: write` ist im Workflow gesetzt. Es werden keine eigens benannten Repository-Secrets referenziert.
- Der lokale Git-Zugang wurde erfolgreich auf SSH umgestellt: `git@github.com:Moritz2011/flugcrawler.git`. Der vorhandene Schlüssel funktionierte; Schlüsselmaterial gehört nicht in diese Dokumentation oder ins Repository.
- Amadeus-, Skyscanner- oder E-Mail-Zugangsdaten sind weder im verifizierten Code noch im Workflow eingebunden.
- Es gibt keine `.env`-Konfiguration im untersuchten Bestand. `.env` ist momentan auch nicht ausdrücklich durch die verfolgte `.gitignore` geschützt. Bei einer später beauftragten Schlüssel-Integration muss der Umgang mit Secrets zuerst sauber eingerichtet werden.

Ein privates Repository ist nicht automatisch ein geschütztes Pages-Login. GitHub weist bei Publishing-Konfigurationen darauf hin, dass Pages-Seiten abhängig von Plan und Konfiguration auch aus privaten Repositories öffentlich erreichbar sein können; siehe die oben verlinkte offizielle Dokumentation. Ein ausschließlich clientseitig eingebautes Passwort wäre kein wirksamer Zugriffsschutz für ausgelieferte Dateien.

## C. Bereits implementierte und nur geplante Funktionen

| Funktion | Umsetzung und Abhängigkeiten | Stand und Einschränkungen |
| --- | --- | --- |
| Statisches Reisefenster | `build_combinations()` und Konstanten in `crawler.py`; daraus entstehen alle Suchdaten | Implementiert und isoliert geprüft; sechs zulässige Kombinationen. Keine Eingabevalidierung für beliebige neue Konfigurationen. |
| Ryanair-Preisabfrage | `fetch_ryanair()`; `requests`, FareFinder-Antwortformat | Durch historische Daten und Logs nachgewiesen. Aktuelle API-Stabilität nicht geprüft. |
| Eurowings-/Condor-Abfrage | `fetch_eurowings()`, `fetch_condor()` | Adaptercode vorhanden, erfolgreiche Preisgewinnung nicht nachgewiesen; das fachliche Ziel ist offen. |
| Airlineunabhängige Auswertung | `merge_cheapest()`, anschließend Kombinationen in `run()` | Rechenlogik implementiert. Kann verschiedene Airlines für Hin-/Rückflug wählen, sofern Daten vorhanden sind. Aktuell nur Ryanair als beobachtete Quelle. |
| Gesamtkosten und Ranking | Summe beider Einzelflug-Minimalpreise; gültige Kombinationen sortiert | Implementiert. Kein Vergleich mit separaten Hin-/Rücktarifen eines Rundreiseangebots, keine Tarif-/Gepäcknormalisierung. |
| Historie | Lesen/Schreiben von `flight_data.json` in `run()` | Implementiert; tagesweise Überschreibung, keine Intraday-Daten. |
| Tabellendashboard | `generate_dashboard()` | Implementiert; sortierte Tabelle, Preise/Airlines, beste Kombination und Zeitstempel. Vom Nutzer gestalterisch akzeptiert. |
| Preisverlauf | Chart.js und eingebettete Daten aus `best.total` | Implementiert; letzte 30 gespeicherte Tage, nicht zwingend 30 Kalendertage. Die günstigste Kombination kann von Tag zu Tag wechseln. |
| Preistrend pro Kombination | `get_trends()` und `trend_badge()`; gleiche Hin-/Rückdaten als Schlüssel | Implementiert und isoliert geprüft; vergleicht mit letztem früheren gespeicherten Tag. Unterschiede unter 0,50 EUR gelten als gleich. |
| Suchlink | `gf_url()` und Link in jeder Zeile | Implementiert als Google-Flights-Navigation. Kein direkter Airline-Buchungslink und keine Buchungsfunktion. |
| Täglicher Cloud-Lauf | `.github/workflows/crawler.yml` | Historisch erfolgreich. Heutiger Aktivierungszustand offen; nicht wieder aktivieren ohne Auftrag. |
| Öffentliche Website | GitHub-Pages-Einstellung außerhalb des Codes | Historisch erfolgreich. Heutiger Zustand und allgemeine Auto-Deployment-Kette nicht abschließend belegt. |
| Preisalarm per E-Mail / Push | Im Gespräch als mögliche Erweiterung vorgeschlagen | Nicht ausgewählt und nicht implementiert. Kein aktueller Entwicklungsauftrag. |
| Amadeus / Skyscanner | Als Alternative diskutiert | Nicht integriert. Kein bestätigtes Konto, keine geprüfte Abdeckung und keine hinterlegte Konfiguration. |
| Playwright / Selenium | Als möglicher Scraping-Ansatz diskutiert | Nicht Teil des Repositorys, kein implementierter Browser-Crawler. |
| Lokales macOS-Setup | Früher `setup.sh` / LaunchAgent als Alternative | Durch Cloud-Entscheidung abgelöst; heute kein nachgewiesenes lauffähiges Setup im Projekt. |

## D. Entscheidungen und ihre Hintergründe

### D.1 Dashboard statt primärer Benachrichtigung

**Gespräch:** Der Nutzer wollte ausdrücklich eine kleine HTML-Seite als Tabelle, die jederzeit geöffnet werden kann. Push-Nachrichten oder ein nur im damaligen Assistenten verfügbares Artifact wurden nicht gewählt. Die akzeptierte Oberfläche soll bei künftigen Änderungen grundsätzlich erhalten bleiben. E-Mail-Alarme sind keine bereits zugesagte Kernfunktion.

### D.2 GitHub Actions statt lokalem Mac-Zeitplan

**Gespräch und Workflow:** Zunächst wurde ein lokaler LaunchAgent geplant. Der Nutzer fragte nach Ausführung bei ausgeschaltetem Laptop und entschied sich für GitHub Actions. Damit entfällt die Abhängigkeit vom eingeschalteten Mac. Ein NAS als Speicherort des lokalen Codes ändert daran nichts; das NAS führt den Python-Job nicht automatisch aus.

Diese Architektur bleibt die zuletzt akzeptierte Ausführungsarchitektur. Aktuell gilt allerdings der spätere Stilllegungswunsch.

### D.3 GitHub Pages und `index.html`

**Gespräch und Code:** Die HTML-Datei wurde für Pages von einer lokalen Dashboard-Datei auf `index.html` umgestellt. Pages sucht einen Einstiegspunkt im ausgewählten Publishing-Verzeichnis; [GitHub beschreibt dafür `index.html`](https://docs.github.com/en/pages/getting-started-with-github-pages/troubleshooting-404-errors-for-github-pages-sites). Ein separater Webserver ist nicht erforderlich.

Der aus GitHub automatisch sichtbare Workflow `pages-build-deployment` ist von `crawler.yml` zu unterscheiden. Er erstellt keine Airline-Abfragen und ist nicht selbst der Preis-Crawler.

### D.4 Dateifenster statt fünf fest codierter Paarungen

**Gespräch und Commit `3bd5a61`:** Der Nutzer wählte den festen Zeitraum 22.–26.10.2026 und mindestens zwei Nächte. Daraus wurden automatisch sechs Paarungen erzeugt, einschließlich 24. → 26. Oktober. Eine dynamische Benutzeroberfläche zum Ändern des Zeitraums wurde ausdrücklich nicht gewählt.

Die sechs Kombinationen und die Mindestnächte dürfen bei einer bloßen Fehlerkorrektur nicht wieder auf die früheren fünf Paarungen zurückfallen.

### D.5 Preis wichtiger als Airline

**Gespräch:** Der Nutzer betonte mehrfach, dass die Airline egal sei. Die Zusammenführung darf daher nicht unnötig auf Ryanair oder identische Airlines beider Richtungen beschränkt werden. Dass heute nur Ryanair vorkommt, ist eine Einschränkung der Datenbeschaffung und keine fachliche Präferenz.

### D.6 Direkte HTTP-Abfragen als erste Implementierung

**Gespräch und Code:** Direkte Airline-Endpunkte wurden verwendet, um ohne echten Browser an strukturierte Daten zu gelangen. Ryanair lieferte historische Daten. Eurowings und Condor wurden zunächst fälschlich als funktionierend beziehungsweise robust genug dargestellt; später räumte der frühere Assistent ein, die Endpunkte geraten zu haben.

Dieser Ansatz ist für Ryanair historisch belegt, aber keine bestätigte Lösung für eine vollständige Airline-Suche. Die nicht validierten Adapter sind technische Schulden, keine verbindlich beizubehaltende Anbieterentscheidung.

### D.7 Browser-Scraping und API-Alternativen

**Gespräch:** Skyscanner wurde vom Nutzer wegen der gewünschten breiten Abdeckung angesprochen. Der frühere Assistent verwies auf JavaScript, Bot-Erkennung und mögliche Captchas und empfahl später Amadeus. Ein tatsächlicher Wechsel wurde nicht implementiert oder abschließend ausgewählt.

Folgende frühere pauschale Aussagen dürfen nicht als gesichertes Projektwissen übernommen werden:

| Frühere Aussage | Belastbare Einordnung für die Weiterentwicklung |
| --- | --- |
| Ein Browser umgeht die damalige Sandbox-Netzwerksperre automatisch. | Nicht belegt. Browser benötigen ebenfalls erlaubten Netzwerkzugang. |
| GitHub Actions könne wegen fehlendem Display keinen Browser verwenden. | Als generelle Aussage falsch. Headless-Browser-Automatisierung ist technisch möglich; sie ist hier lediglich nicht implementiert. |
| Skyscanner habe keine API mehr. | So pauschal nicht zutreffend. Es gibt offizielle [Skyscanner Travel API-Dokumentation für Partner](https://developers.skyscanner.net/docs/intro). Zugang, Konditionen und Nutzbarkeit für dieses Projekt müssen separat geprüft werden. |
| Amadeus decke automatisch alle Airlines einschließlich Ryanair, Eurowings und Condor kostenlos ab. | Für dieses Projekt nicht nachgewiesen. Weder Verfügbarkeit, Zugang, Preisplan noch konkrete Route-/Airline-Abdeckung wurden validiert. Die Entwicklerseite lieferte beim bisherigen Abruf keinen auswertbaren Inhalt; keine aktuelle Integrationszusage ableiten. |
| Fehlende Eurowings-/Condor-Preise bedeuteten, dass der Flugplan noch nicht veröffentlicht sei. | Nicht nachgewiesen. Die Adapter selbst sind nicht validiert; fehlende Treffer erlauben keine Aussage über den tatsächlichen Buchungsbestand. |
| Ein nicht verlinktes öffentliches Dashboard werde sicher nicht gefunden oder indexiert. | Nicht zugesichert; keine belastbare Zugriffsschutzmaßnahme. |
| Ein JavaScript-Passwort schütze eine statische öffentliche Seite zuverlässig. | Kein wirksamer Schutz der bereits ausgelieferten Inhalte; wurde auch nicht implementiert. |

Keine neue API allein aufgrund dieser alten Empfehlungen einbauen. Erst anhand echter, nachvollziehbarer Angebote und zulässiger Zugangsmöglichkeiten evaluieren.

### D.8 Öffentliches Repository zunächst akzeptiert, später Stilllegung gewünscht

**Gespräch / Remote-Beobachtung:** Öffentliches Hosting wurde wegen der zunächst als unkritisch betrachteten Preise akzeptiert. Später wollte der Nutzer keine automatische Suche und keine öffentlich sichtbare Website mehr, den Code aber behalten. Es wurden Anleitungsschritte für Workflow-Deaktivierung, Pages-Abschaltung und privates Repository gegeben. Nur die Repository-Sichtbarkeit `private` ist inzwischen konkret beobachtet; die übrigen Schritte sind nicht durch eine abschließende Statusprüfung belegt.

Dieser spätere Betriebswunsch hat Vorrang vor älteren Aussagen wie „läuft ab jetzt jeden Morgen“.

### D.9 Bestehenden Projektordner verwenden

**Gespräch und zuletzt ausgeführte Synchronisierung:** Der Nutzer arbeitet in VS Code mit seinem bestehenden NAS-Repository. Er möchte keinen zusätzlichen Projektordner, keine parallelen Kopien und keine Änderungen am falschen importierten Demo-Bestand.

Bei der Vorbereitung wurde zunächst irrtümlich eine separate Kopie erstellt. Danach wurde der tatsächliche geöffnete NAS-Ordner identifiziert und dort synchronisiert. Der zusätzliche Checkout wurde aus dem Arbeitsbereich in eine temporäre Ablage verschoben. Für zukünftige Arbeiten stets zuerst `pwd`, Git-Root und `git status` prüfen; nicht aufgrund eines älteren Chat-Ausgabepfads an einer anderen Kopie arbeiten.

## E. Anforderungen und Entwicklungsrichtlinien

### E.1 Verbindliche fachliche Leitplanken

- Airlineunabhängig den niedrigsten belegten Gesamtpreis ermitteln; Umfang der tatsächlich abgefragten Quellen offenlegen.
- Mindestens zwei Nächte respektieren; bei unverändertem historischen Fenster müssen sechs Kombinationen entstehen.
- Tabellenansicht, Preisverlauf und Trendindikatoren erhalten.
- Kein interaktiver Konfigurationsausbau ohne neuen Wunsch; Datenbereich darf statisch im Code bleiben.
- Keine Buchung, kein automatischer Kauf und keine Zahlungen.
- Keine Behauptung eines global günstigsten Angebots bei unvollständigen Datenquellen.
- Der derzeit nicht benötigte Tracker soll nicht beiläufig durch Tests wieder aktiviert werden.

### E.2 UI-Vorgaben aus dem akzeptierten Bestand

Es gibt kein eigenständiges Designsystem oder schriftliches Styleguide. Der Nutzer bewertete die bestehende Dashboard-Vorschau positiv. Die produktive Umsetzung folgt diesem Muster:

- Deutsche Beschriftungen und Wochentage.
- Blauer Verlauf im Kopfbereich, heller Seitenhintergrund.
- Weiße Tabelle, grün hervorgehobenes Bestangebot und grüne Preiskarte.
- Datumsangaben, Nächte, Einzelflugpreise mit Airline, Gesamtpreis und Suchbutton je Zeile.
- Grün für günstigere, rot für teurere und grau für nahezu gleiche Preise.
- Begrenzte Inhaltsbreite von 1000 Pixeln und Chart darunter.

Ein Viewport-Meta-Tag und responsive Chart-Einstellung sind vorhanden. Eine vollständige mobile Tabellenoptimierung oder Barrierefreiheitsprüfung ist nicht nachgewiesen. Preise verwenden technisch formatierte Dezimalpunkte; eine durchgehend deutsche Währungsformatierung wurde nicht implementiert.

### E.3 Sicherheit und Datenintegrität

Zugangsdaten niemals in Chat, Quellcode, Dokumentation, JSON-Historie oder HTML übernehmen. Für eine spätere API-Integration wären lokal geschützte Umgebungsvariablen und in CI GitHub Secrets zu verwenden; konkrete Namen sind noch nicht vereinbart.

Historische Preisstände sind für Vergleiche relevant und sollen bei Änderungen nicht versehentlich durch Demo-Daten ersetzt oder gelöscht werden. Auch bei einer späteren Neusuche muss die fehlende Trennung verschiedener Suchkonfigurationen berücksichtigt werden.

Ein lokaler Crawler-Lauf schreibt Ergebnisdateien. Er ist daher kein rein lesender Funktionstest. Beim Import kann das Skript bereits ein fehlendes Paket automatisch installieren. Tests für Dokumentations- oder Analyseaufgaben sollen diesen Import vermeiden.

### E.4 Performance und Arbeitsweise

Die Zielgröße war eine kleine tägliche Suche, kein dauerhaft laufender Dienst und keine Echtzeitsuche. Eine garantierte Laufzeit wurde nicht vereinbart. Bei sechs unterschiedlichen Richtungs-/Datumspunkten entstehen bis zu 26 Anwendungsebene-HTTP-Aufrufe pro Lauf einschließlich Eurowings-Fallback und Session-Startseiten, ohne mögliche Redirects mitzuzählen. Der Code arbeitet diese sequenziell ab.

Der Nutzer bevorzugt konkrete Umsetzung und verständliche Schritt-für-Schritt-Erklärungen. Für dieses Projekt besonders wichtig:

- Im bereits geöffneten Projekt arbeiten.
- Versionsstand zuerst abgleichen; `M` steht für lokale Abweichungen gegenüber dem Git-Index, nicht automatisch für eine neuere oder ältere GitHub-Version.
- Vorhandene Änderungen nicht ungeprüft verwerfen.
- Keine Tokens oder Passwörter im Chat anfordern.
- Angeforderte Arbeitsschritte einhalten: Die Dokumentation wurde ausdrücklich erst nach der lokalen Synchronisierung wieder freigegeben.
- Keine erfundenen Endpunkte oder vermuteten Fehlerursachen als gelöste Probleme präsentieren.
- Für diese Übergabe ausschließlich diese Markdown-Datei schreiben; nichts installieren, keinen Workflow auslösen und keinen Commit erzeugen.

### E.5 Bestehende Codekonventionen

Der Bestand verwendet `snake_case` für Funktionen, Großbuchstaben für globale Konstanten, einfache Dictionaries als Modelle und überwiegend deutsche Kommentare, teilweise mit ASCII-Umschreibung. HTML und CSS liegen im Python-F-String. CSS-/JavaScript-Klammern sind deshalb im Template als `{{` und `}}` geschrieben.

Es gibt keine konfigurierte Formatierung, keinen Linter, keinen Typprüfer und keine festgeschriebene Testkonvention. Keine zusätzlichen Konventionen als historisch vereinbart darstellen.

## F. Bekannte Fehler, Einschränkungen und technische Schulden

### F.1 Bestätigte funktionale Lücken und beobachtete Probleme

| Thema | Beleg / Auswirkung | Bisheriger Versuch / Zustand |
| --- | --- | --- |
| Nur Ryanair liefert beobachtete Daten | Alle 164 gespeicherten Tagesstände enthalten ausschließlich Ryanair. Letzter geprüfter Lauf: Ryanair 3+3 Ergebnisse, Eurowings/Condor jeweils 0+0. | Zweiter Eurowings-Endpunkt und toleranteres Condor-Parsen ergänzten keinen nachgewiesenen Erfolg. Offen. |
| Grüner Workflow ist kein Vollständigkeitsnachweis | Adapter unterdrücken viele Fehler; auch ohne Preise endet `run()` regulär. | Erfolgsmeldungen im Gespräch waren teilweise zu weitgehend. Eine Quellenstatusprüfung ist nicht implementiert. |
| Andere HTTP-Statuscodes bleiben still | `if r.status_code == 200` ohne aussagekräftigen `else`-Zweig. | Grund für null Treffer aus den Logs nicht bestimmbar. Offen. |
| UTC-Zeitplan entspricht nicht ganzjährig 08:00 Berlin | Fester Cronwert, kein DST-Ausgleich; YAML-Kommentare sind unzutreffend. | Nicht geändert. |
| Reisefenster abgelaufen | 22.–26.10.2026 ist zum Dokumentationsdatum vorbei; kein Schutz vor vergangenen Reisedaten. | Vor einem späteren Wiederanlauf neue Daten vereinbaren. |
| Feste Datums- und Routentexte | HTML-Titel, Untertitel und Suchlink bleiben unabhängig von neuen Konstanten teilweise fest. | Neue Suche würde zusätzliche Anpassungen verlangen. |
| Unvollständiges Preis-/Flugmodell | Nur Tagesminimum, Airline und Summe; keine Flugnummer, Gepäck-/Tarifdaten oder belastbare Buchungsreferenz. | Das Dashboard ist ein Preisindikator, keine verifizierte Buchungsübersicht. |

### F.2 Aus dem Code ableitbare Robustheitsgrenzen

Diese Punkte sind strukturell erkennbar; es ist nicht belegt, dass jeder davon bereits einen Produktionsfehler ausgelöst hat:

- **Ungültige JSON-Historie:** `json.load()` hat keine Wiederherstellung bei beschädigter oder unerwarteter Datei. Ein solcher Fehler erreicht den äußeren Traceback-Handler.
- **Nicht atomisches Speichern:** JSON und HTML werden direkt überschrieben. Ein Abbruch kann eine teilweise geschriebene Datei oder ein Paar unterschiedlicher Generationen hinterlassen.
- **Parallele Läufe:** Es gibt weder eine Actions-`concurrency`-Gruppe noch eine Dateisperre für die Ergebnisdateien. Gleichzeitige Läufe könnten Aktualisierungen überschreiben oder beim Push kollidieren.
- **Antwortvalidierung:** Die Adapter setzen bestimmte Datentypen und Antwortstrukturen voraus. Zahlen als Strings werden nicht überall gleich behandelt. Betrag, Währung, Reisedatum und tatsächlicher Angebotskontext werden nicht umfassend validiert.
- **Mögliche Fehlzuordnung beim Fallback:** Der Eurowings-Fallback weist den gefundenen Betrag dem angefragten Datum zu, ohne ein passendes Angebotsdatum zu verifizieren.
- **Abdeckung nicht messbar:** Nur die Gewinner pro Tag werden persistiert. Es fehlen Status, Abrufzeit und Rohangebote je Quelle; aus der Historie lässt sich daher nicht entscheiden, ob eine andere Airline teurer war, scheiterte oder gar nicht angeboten wurde.
- **Tagesweise Überschreibung:** Mehrere tägliche Läufe erzeugen keinen detaillierteren Verlauf.
- **Keine Trennung verschiedener Suchaufträge:** Historische Tagesbestpreise werden auch nach einem geänderten Fenster gemeinsam gezeichnet. Für andere Strecken oder neue Reisen wären solche Werte unter Umständen nicht sinnvoll vergleichbar.
- **Trend-Schwelle:** Änderungen von weniger als 0,50 EUR erscheinen als gleich. Die ursprüngliche Nutzerbeschreibung unterschied nur günstiger/teurer/gleich; diese Toleranz ist eine Implementierungsentscheidung ohne dokumentierte fachliche Begründung.
- **Trend-Vergleichstag:** Verglichen wird der unmittelbar letzte gespeicherte frühere Tag, nicht zwingend gestern und nicht der letzte Tag mit gültigem Preis für diese Kombination. Fehlende Vergleichspreise ergeben keinen Trend.
- **Chart-Zeitraum:** Letzte 30 Einträge können mehr als 30 Kalendertage umfassen. `spanGaps: true` verbindet Punkte über Datenlücken hinweg.
- **Unbegrenztes Wachstum:** Die gesamte JSON-Historie wird jedes Mal gelesen und geschrieben, obwohl der Chart nur einen Ausschnitt zeigt.
- **Ungebundene Abhängigkeit:** `requests` hat weder Versionsgrenze noch Lockfile; `ubuntu-latest` und Action-Hauptversions-Tags sind ebenfalls bewegliche Laufzeitbestandteile.
- **Import-Nebenwirkungen:** Automatische Paketinstallation und Umkonfiguration von Standardausgaben erschweren gefahrlose Tests und die Verwendung als Bibliothek.
- **Browser-CDN-Abhängigkeit:** Bei blockiertem Chart.js bleibt die statische Tabelle lesbar, das Diagramm kann aber nicht initialisiert werden. Kein Offline-Fallback.
- **Monolithisches Template:** Darstellung, Datenverarbeitung und Providerzugriffe sind in einer Datei gekoppelt. Direkte Templateänderungen müssen F-String-Klammern berücksichtigen.
- **HTML-Escaping:** Die Templatewerte werden nicht allgemein escaped. Aktuelle Airlinenamen sind feste Strings; bei späteren frei übernommenen Datenfeldern müsste die Ausgabe abgesichert werden. Ein tatsächlicher Angriff ist nicht bekannt.

### F.3 Historische Probleme und ihr Status

1. **Cowork-Netzwerksperren:** Frühere Fetch-/Python-Aufrufe scheiterten mit Allowlist-/Proxyfehlern. App-Neustarts und Domainfreigaben wurden versucht. Dass ein bestimmter „Allowlist-Bug“ die Ursache war, wurde nicht belastbar bestätigt. Diese alte Umgebung ist nicht mit dem aktuellen lokalen Git-/NAS-Problem gleichzusetzen.
2. **Fehlender Actions-Workflow nach Upload:** Der Nutzer sah zunächst nur Pages. Als Erklärung wurde der versteckte `.github`-Ordner beim Finder-/Browserupload genannt. Nach manuellem Anlegen war der Workflow sichtbar. Den Workflowpfad beim Übertragen erhalten.
3. **Fehlgeschlagener Actions-Lauf mit Exitcode 1:** Ein historischer Fehler wurde gemeldet. Der konkrete Traceback wurde damals nicht verfügbar gemacht. UTF-8/Emojis wurden als vermutete Ursache genannt, aber nicht nachgewiesen. Der Code enthält inzwischen UTF-8- und Traceback-Behandlung; die genaue damalige Ursache bleibt offen.
4. **PAT konnte Workflowdatei nicht pushen:** Fehlender `workflow`-Scope eines klassischen Tokens wurde von GitHub ausdrücklich gemeldet. Damals wurde ein Token mit passenden Berechtigungen empfohlen. Der aktuelle lokale Git-Zugang verwendet stattdessen vorhandene SSH-Authentifizierung; kein neues Token nötig.
5. **Veralteter lokaler Git-Stand und `M` auf dem NAS:** Behoben; siehe Abschnitt H. Der anfängliche Import im Assistenten-Arbeitsverzeichnis war nicht das tatsächlich geöffnete VS-Code-Repository.
6. **NAS-Fehler bei `.git/FETCH_HEAD`:** Normaler Fetch scheiterte mit `Invalid argument`. Ohne Schreiben dieser Metadatendatei gelang der Abruf. Nach Neuerstellung der leeren Datei funktionierte auch normaler Fetch wieder. Der zugrunde liegende NAS-/Dateisystemfehler wurde nicht weiter diagnostiziert; bei erneutem Auftreten nicht ungeprüft andere Git-Daten löschen.
7. **Pages-Aktualisierung nach Bot-Push:** Früher wurde ein automatischer Zusammenhang als selbstverständlich erklärt. Der tatsächliche beobachtete Pages-Lauf und die dokumentierte `GITHUB_TOKEN`-Einschränkung müssen bei Wiederbetrieb gemeinsam geprüft werden; siehe B.8.

## G. Offene Aufgaben und mögliche Fortsetzung

Die Prioritäten beziehen sich auf eine **eventuell später beauftragte Wiederaufnahme**. Es besteht derzeit kein Auftrag, diese Liste automatisch abzuarbeiten.

### G.1 Hohe Priorität

| Aufgabe | Herkunft / Stand | Abhängigkeiten |
| --- | --- | --- |
| Stilllegung verifizieren, falls gewünscht | Letzter Betriebswunsch: keine automatische Suche und keine öffentliche Website. Repository privat bestätigt; Workflow-/Pages-Status offen. | Zugriff auf die betreffenden GitHub-Einstellungen; keine Testauslösung zur Statusprüfung. |
| Neue Suchdaten vor einem Wiederanlauf klären | Altes Fenster liegt in der Vergangenheit. Kein neuer Zeitraum genannt. | Neue Nutzerentscheidung. Nicht stillschweigend auf ein anderes Jahr umstellen. |
| Reale airlineübergreifende Datenquelle herstellen | Wiederholter ausdrücklicher Nutzerwunsch; Eurowings/Condor bislang nicht erfolgreich. | Valider Zugang, nachgewiesene Route-/Datumsabdeckung und Vergleich mit tatsächlichen Angeboten. Anbieterwahl ist offen. |
| Quellenfehler von echten Nullangeboten unterscheiden | Aus dem Code erkennbare Lücke; erklärt die unzuverlässige Aussagekraft eines grünen Jobs. | Geeignete HTTP-/Schema-/Quellenstatusbeobachtung bei der späteren Adapterarbeit. |

### G.2 Mittlere Priorität

- **Veröffentlichungskette bei Wiederbetrieb prüfen:** Ergebniscommit allein ist kein nachgewiesener Pages-Trigger. Erst Repository-Datei und tatsächlich ausgelieferten HTML-Stand vergleichen. Aktuell keine Veröffentlichung vornehmen.
- **Zeitplan präzisieren:** Gewünschte Uhrzeit beziehungsweise DST-Verhalten klären und den falschen YAML-Kommentar korrigieren, sobald Workflowpflege beauftragt ist.
- **Neue Datenkonfiguration konsistent darstellen:** Bei künftigen Fenstern auch Titel, Untertitel, Suchlinks und die Vergleichbarkeit alter Historie berücksichtigen.
- **Dauerhafte Tests ergänzen:** Es gibt noch keine versionierte Testsuite. Die aktuell isoliert geprüften Funktionen bilden konkrete Ausgangsfälle; siehe J. Dies ist abgeleiteter Qualitätssicherungsbedarf, keine bereits erledigte Implementierung.
- **Fehler-/Schreibrobustheit bewerten:** Beschädigte Historie, atomische Ausgaben und konkurrierende Läufe sind erkennbare technische Schulden. Kein Umfang einer konkreten Überarbeitung vereinbart.

### G.3 Niedrige Priorität beziehungsweise vorgeschlagene, nicht ausgewählte Funktionen

- Direkte Airline-Buchungslinks statt Google-Flights-Suche wurden vorgeschlagen, aber nicht ausgewählt. Vorher müssten echte Angebots- oder Flugidentifikatoren verfügbar sein.
- E-Mail- oder Push-Preisalarm mit Schwellenwert wurde vorgeschlagen, aber nicht beauftragt; weder Dienst noch Schwellenwert noch Zustellziel sind festgelegt.
- Eine präzisere Erläuterung des Trend-Vergleichstags und der 0,50-EUR-Schwelle wäre eine nachvollziehbare UI-Korrektur, aber kein neuer bestätigter Produktauftrag.

### G.4 Langfristige Optionen ohne vereinbarte Roadmap

Eine offizielle Aggregator-API oder ein browsergestützter Abruf wurden als Alternativen diskutiert. Die konkrete Auswahl ist offen. Ein verfügbares Assistenten-Tool für Flugsuche wäre nicht automatisch eine im täglichen GitHub-Job nutzbare API-Integration.

Mehrbenutzerbetrieb, Datenbankmigration, neue Strecken, mobiles App-Frontend, zusätzliche Reiseprodukte oder ein kommerzieller Betrieb sind nicht dokumentiert beauftragt. Eine interaktive Datumsverwaltung wurde zugunsten statischer Konfiguration gerade nicht gewählt.

## H. Aktueller und letzter Arbeitsstand

### H.1 Letzte tatsächliche Codeentwicklung

Die verfolgte Implementierung stammt aus zwei fachlichen Commits:

| Commit | Inhalt |
| --- | --- |
| `ada0d31` vom 29.04.2026 | Erste im Repository erhaltene Implementierung mit fünf festen Kombinationen, Airline-Abfragen, Historie, HTML und Workflow. |
| `3bd5a61` vom 30.04.2026 | Dynamische Kombinationen aus festem Datumsfenster, Trendanzeige und Überarbeitung der Adapter-/Fehlerbehandlung. |

Danach finden sich laufende Ergebnisupdates. Der letzte Ergebniscommit ist `58f9bce` vom 09.10.2026. Eine spätere erfolgreiche Amadeus-, Skyscanner-, Eurowings- oder Condor-Integration ist weder im Code noch in der Historie vorhanden.

### H.2 Letzte Remote-Laufbeobachtung

In der Vorbereitung dieser Übergabe wurden GitHub-Daten gelesen:

- Crawler-Lauf [`37928177578`](https://github.com/Moritz2011/flugcrawler/actions/runs/37928177578), ausgelöst durch `schedule` am 09.10.2026 um 12:09:15 UTC, Ergebnis `success`.
- Der zugehörige Job meldete sechs Kombinationen, Ryanair dreimal je Richtung und Eurowings sowie Condor jeweils null Ergebnisse.
- Tagesbestpreis: historisch 174,69 EUR, 22.10. → 26.10., beide Richtungen Ryanair.
- Pages-Lauf [`37928219104`](https://github.com/Moritz2011/flugcrawler/actions/runs/37928219104) zum Ergebniscommit `58f9bce`, ebenfalls erfolgreich.

Diese Beobachtungen beschreiben alte Läufe. Sie beweisen keine heute aktive Automatisierung, keine aktuelle Angebotsverfügbarkeit und keine heute öffentliche Website. Bei privaten Repositories benötigen die Links entsprechende Zugriffsrechte.

### H.3 Lokale Synchronisierung unmittelbar vor der Dokumentation

Der tatsächliche in VS Code geöffnete Ordner liegt auf einem NAS. Er stand zunächst noch auf `ada0d31`, obwohl `crawler.py` bereits den aktuellen Inhalt von GitHub enthielt. Zusätzlich meldete Git ausführbare Dateirechte gegenüber dem gespeicherten Modus `100644`. `flight_data.json` und `index.html` fehlten lokal.

Die Synchronisierung wurde anschließend **im bestehenden NAS-Repository** durchgeführt:

1. Bestehende SSH-Authentifizierung erfolgreich geprüft; kein Passwort oder Token entgegengenommen.
2. Lokalen Remote `origin` auf die SSH-URL des bestehenden Repositorys umgestellt.
3. Aktuelle Remote-Historie abgerufen.
4. Bestehende Inhalte aller vorhandenen verfolgten Dateien bytegenau mit dem aktuellen Remote-Stand verglichen; keine abweichenden Nutzer-Codeinhalte verworfen.
5. Fehlende Ergebnisdateien aus dem Remote-Commit ergänzt.
6. Lokalen Branch und Index auf den bereits existierenden, nachfolgenden Commit `58f9bce` vorgezogen; kein neuer Commit erstellt.
7. Lokal `core.filemode=false` gesetzt, damit NAS-Dateirechte keine scheinbaren Codeänderungen verursachen.
8. Finder- und Editor-Metadaten lokal über `.git/info/exclude` ausgeschlossen: `/.DS_Store` und `/.vscode/`. Diese Regeln sind keine Änderungen an der verfolgten `.gitignore`.
9. Leere problematische `.git/FETCH_HEAD` erneuert und einen normalen `git fetch origin` erfolgreich geprüft.
10. Abschließend `working tree clean` und Ahead/Behind `0 / 0` bestätigt.

Die lokale Git-Konfiguration und `.git/info/exclude` werden nicht mitgeklont. Bei einer späteren anderen Arbeitskopie insbesondere auf NAS-Dateirechte achten; nicht einfach Dateimodusänderungen committen.

Die zwischenzeitlich irrtümlich angelegte zusätzliche Kopie wurde aus dem Assistenten-Arbeitsbereich entfernt und nur temporär gesichert. Sie ist nicht der zu verwendende Projektstamm. Ein alter importierter Demo-Ordner ist ebenfalls keine maßgebliche Arbeitskopie.

### H.4 Was mit dieser Übergabe abgeschlossen wird

Die erneute Analyse bezieht sich auf das synchronisierte NAS-Repository. Es wurden 16 isolierte Funktionsprüfungen am dortigen Quellcode erfolgreich durchgeführt. Jetzt wird ausschließlich `PROJECT_HANDOVER.md` angelegt und anschließend auf Vollständigkeit sowie unveränderte übrige Dateien geprüft.

Die nächsten tatsächlichen Schritte bestimmt der Nutzer. Es gibt keinen offenen begonnenen Code-Patch und keine erteilte Freigabe zum Wiederaktivieren der Automatisierung. Der sichtbare Gesprächsstand ist hierfür nachvollziehbar; nicht sichtbare frühere Chats oder nicht zugängliche GitHub-Einstellungen bleiben ausdrücklich unberücksichtigt.

## I. Installation, Start und Entwicklungsumgebung

### I.1 Voraussetzungen

- Vorhandenes Git-Repository und, für private Remote-Zugriffe, authentifizierter GitHub-Zugang.
- Python: In Actions ausdrücklich Version 3.11. Im lokalen Analyse-Terminal war Python 3.9.6 verfügbar; damit wurden Syntax und ausgewählte Funktionen geprüft. Das ist keine vollständige Freigabe sämtlicher HTTP-Funktionen für alle Python-Versionen. Eine formale Mindestversion ist nicht definiert.
- Python-Paket `requests`.
- Netzwerkzugriff auf die tatsächlich verwendeten Quellen für echte Abfragen; CDN-Zugriff im Browser für das Diagramm.
- Schreibzugriff neben `crawler.py`, weil dort die beiden Ergebnisdateien liegen.
- Für die lokale NAS-Arbeitskopie muss das Volume gemountet und erreichbar sein. Actions ist vom lokalen Mount unabhängig.

### I.2 Zuerst sichere Zustandsprüfung

Die folgenden Befehle wurden im tatsächlichen Projekt verwendet und sind rein prüfend:

```bash
pwd
git rev-parse --show-toplevel
git --no-optional-locks status --short --branch
git rev-list --left-right --count HEAD...origin/main
python3 --version
```

`origin/main` beschreibt den zuletzt abgerufenen Stand. Ein `0 / 0` ohne frischen Remote-Abruf belegt allein nicht, dass seitdem auf GitHub nichts Neues passiert ist. Der normale Befehl `git fetch origin` wurde nach der NAS-Metadatenkorrektur erfolgreich ausgeführt. Bei einer reinen Dokumentationsaufgabe muss jedoch kein erneuter Fetch Schreibzugriffe auf Git-Metadaten erzeugen.

### I.3 Abhängigkeiten und echter Lauf

Im Workflow tatsächlich dokumentierte Befehle:

```bash
pip install -r requirements.txt
python crawler.py
```

Diese Befehle wurden im Rahmen dieser Dokumentation **nicht ausgeführt**, weil sie Pakete installieren beziehungsweise echte Abfragen starten und Ergebnisdateien verändern würden.

Auf einem Mac heißt der gewünschte Interpreter häufig `python3`; entsprechend wären `python3 -m pip install -r requirements.txt` und `python3 crawler.py` naheliegende lokale Varianten. Diese Varianten sind hier als **nicht als vollständiger Live-Lauf geprüfte Anweisungen** gekennzeichnet. Zuerst den Interpreter und den Schreib-/Suchkontext prüfen. Keine neue virtuelle Umgebung oder Abhängigkeiten nur zum Lesen dieses Dokuments anlegen.

Es gibt keine zusätzlich erforderlichen Anwendungs-Umgebungsvariablen, keine Datenbankmigration und keinen gesonderten Buildschritt. Die beiden UTF-8-/Ausgabevariablen stammen aus dem vorhandenen Workflow und sind keine Secrets.

**Startwirkung:** Ein echter Lauf ersetzt den heutigen JSON-Tagesstand und generiert `index.html` neu, auch wenn keine Quelle Daten liefert. Wegen des vergangenen Reisefensters und des Stilllegungswunsches nicht ohne neuen Auftrag ausführen.

### I.4 Lokale Anzeige

Die bestehende `index.html` kann als statische Datei im Browser geöffnet werden. Es ist kein Python-Webserver für die Preisabfrage nötig. In dieser Dokumentationsrunde wurde kein Browser-Rendering oder interaktiver Linktest durchgeführt. Der HTML-Inhalt wurde dagegen aus der gespeicherten Historie vollständig im Speicher reproduziert.

### I.5 Deployment und Reaktivierung nur bei neuem Auftrag

Für die historische Cloud-Ausführung benötigt GitHub die Workflow-Datei im Standardbranch. Ein manueller Lauf ist wegen `workflow_dispatch` vorgesehen. Pages wurde separat mit `main` und `/ (root)` eingerichtet.

Vor einer späteren Reaktivierung prüfen:

1. Neue gültige Reisedaten und weiterhin gewünschte Preisbedingungen.
2. Aktivierungszustand des Crawler-Workflows und gewünschte Zeitplansemantik.
3. Nachgewiesene Datenquellen und Umgang mit Nulltreffern/Fehlern.
4. Pages-Publishing-Konfiguration und tatsächlicher Deployment-Trigger.
5. Gewünschte Sichtbarkeit; privater Code und öffentliches Pages-Hosting sind unterschiedliche Einstellungen.

Die letzte Nutzerentscheidung war Stilllegung. Hier wird deshalb bewusst kein automatischer Wiederanlauf vorgenommen. Die [GitHub-Anleitung zum Deaktivieren und Aktivieren von Workflows](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow) und die [Anleitung zum Unpublish einer Pages-Seite](https://docs.github.com/en/pages/getting-started-with-github-pages/unpublishing-a-github-pages-site) beschreiben die getrennten Verwaltungsfunktionen. Das reine Unpublish kann durch eine spätere neue Veröffentlichung rückgängig gemacht werden; für einen ruhenden Tracker daher auch den eigentlichen Crawler deaktiviert halten.

## J. Tests und Qualitätssicherung

### J.1 Vorhandene Tests gegenüber tatsächlich ausgeführten Prüfungen

**Im Repository vorhanden:** Keine automatisierte Testsuite, kein `pytest`, kein `unittest`-Bestand, kein Testworkflow, keine Coverage-Konfiguration und kein Linter. Der Crawler-Actions-Lauf ist ein Produktions-/Ergebnislauf, kein Unit-Test.

**Für diese Übergabe am 14.11.2026 tatsächlich ausgeführt:**

- Syntaxprüfung des tatsächlichen `crawler.py` mittels `ast.parse()`.
- 16 isolierte Prüfungen aus dem vorhandenen Quellcode extrahierter Funktionen.
- JSON-Lesen und Untersuchung aller gespeicherten Kombinationen.
- Vergleich des generierten HTML im Speicher mit der vorhandenen `index.html`.
- Git- und Dateistandsprüfung vor der Dokumentation.

Die Funktionen wurden über den Python-AST ausgewählt und in einem kleinen separaten Namensraum ausgeführt. Das gesamte Modul wurde nicht importiert. `requests`, der Installationsfallback und `run()` wurden nicht ausgeführt. Für `generate_dashboard()` wurde die Dateiausgabe durch einen In-Memory-Puffer ersetzt. Es wurden keine Testdateien angelegt.

### J.2 Ergebnisse der 16 isolierten Prüfungen

| Nr. | Prüfung | Ergebnis |
| --- | --- | --- |
| 1 | Genau sechs gültige Kombinationen im Fenster, jeweils mindestens zwei Nächte | bestanden |
| 2 | Kombination 24.10. → 26.10. enthalten | bestanden |
| 3 | Ein zu kurzes Fenster liefert keine Kombinationen | bestanden |
| 4 | Niedrigerer Preis aus anderer Quelle wird ausgewählt | bestanden |
| 5 | Leere Quellen-Dictionaries sind zulässig | bestanden |
| 6 | Preisgleichheit erhält die Reihenfolge der zuerst gelieferten Quelle | bestanden |
| 7 | Preisrückgang wird auch bei Lücke zwischen gespeicherten Tagen erkannt | bestanden |
| 8 | Erhöhung um genau 0,50 EUR erzeugt Aufwärtstrend | bestanden |
| 9 | Erhöhung um 0,49 EUR gilt nach aktueller Implementierung als gleich | bestanden |
| 10 | Fehlender Preis ergibt keinen Trend | bestanden |
| 11 | Ohne früheren Tag werden keine Trends ausgegeben | bestanden |
| 12 | Deutscher Wochentag: 22.10.2026 ist `Do` | bestanden |
| 13 | Suchlink enthält Route und beide Reisedaten | bestanden; nur Stringinhalt geprüft |
| 14 | Dashboard aus der letzten gespeicherten Historie entspricht bytegenau der versionierten HTML-Datei | bestanden |
| 15 | HTML-Erzeugung funktioniert ohne Angebote und ohne Bestpreiskarte | bestanden |
| 16 | Sämtliche nichtleeren historischen Gesamtsummen entsprechen der gerundeten Summe der Richtungsbeträge | bestanden |

Diese einmaligen Prüfungen sind **keine dauerhaft hinterlegte Testsuite**. Keine prozentuale Testabdeckung wurde gemessen. Sie validieren keine aktuellen Anbieterantworten und keine heutigen Buchungspreise.

### J.3 Reproduzierbare rein lesende Basisprüfungen

Folgende Befehle entsprechen den hier geprüften Standardbibliotheks-Operationen und verändern keine Projektdateien:

```bash
python3 -B -c 'import ast,pathlib; ast.parse(pathlib.Path("crawler.py").read_text()); print("Syntax OK")'
python3 -B -c 'import json,pathlib; h=json.loads(pathlib.Path("flight_data.json").read_text()); print(len(h), min(h), max(h))'
git --no-optional-locks diff --stat
git --no-optional-locks diff --cached --stat
```

Für Funktionsprüfungen denselben AST-Ansatz verwenden oder nach gesondertem Entwicklungsauftrag den Code testbar modularisieren. Ein einfaches `import crawler` kann durch den Paketinstallationsfallback bereits Nebenwirkungen haben.

### J.4 Manuelle Abnahme bei späteren Änderungen

- Tabelle enthält alle zulässigen Kombinationen, keine Ein-Nacht-Verbindung.
- Die günstigste vollständige Kombination steht vorne und ist hervorgehoben.
- Fehlender Teilflug erzeugt keinen scheinbar vollständigen Gesamtpreis.
- Hin-/Rückflug dürfen unterschiedliche Airlines haben.
- Trend wird für dasselbe Datumspaar berechnet, nicht versehentlich zwischen zwei verschiedenen Tagesbestangeboten.
- Bestpreiskurve verwendet gespeicherte echte Daten, keine Demo-Historie.
- Datum, Route, Währung und Titel stimmen nach einer Konfigurationsänderung zusammen.
- Durch einen gezielt genehmigten Quellenvergleich ist belegt, welche Airlines tatsächlich abgefragt wurden und wie Ausfälle sichtbar werden.
- Bei genehmigtem Deployment tatsächlichen Seiteninhalt und Aktualisierungszeit prüfen; ein grüner Crawler-Lauf reicht nicht.

### J.5 Nicht getestete kritische Bereiche

Nicht aktuell live geprüft wurden Airline-Endpunkte, HTTP-Fehlerpfade, Captcha-/Bot-Schutz, Gebühren-/Gepäckumfang, direkte Buchbarkeit, echte Browserdarstellung, mobile Bedienung, CDN-Ausfall, konkurrierende Läufe, beschädigte Historie, Pages-Zugriffsschutz und die heutigen GitHub-Aktivierungseinstellungen.

Die letzten Logs liefern null Ergebnisse für Eurowings/Condor, aber keine verlässlichen HTTP-Statusdiagnosen. Aus den Prüfungen folgt daher keine Lösung dieser Adapterprobleme.

## K. Konkrete Hinweise für den nächsten KI-Coding-Assistenten

### K.1 Empfohlene Lesereihenfolge

1. Diese Datei, insbesondere Quellenlage, Betriebswunsch und bekannte Quellenprobleme.
2. `crawler.py`: Konstanten, `build_combinations()`, Adapter und `run()`.
3. `crawler.py`: `get_trends()` und `generate_dashboard()`.
4. `.github/workflows/crawler.yml`: Zeitplan, Ausgaberechte und Ergebnis-Commit.
5. `requirements.txt` und `.gitignore`.
6. Einen aktuellen Tagesstand aus `flight_data.json` und die erzeugte `index.html` zum Abgleich; nicht die gesamte generierte Historie ohne konkreten Grund erneut ausgeben.

### K.2 Vor der ersten Änderung

- Sicherstellen, im tatsächlich geöffneten Git-Repository zu arbeiten. Keine neue parallele Arbeitskopie ohne ausdrücklichen Wunsch anlegen.
- Branch, Status und lokale Änderungen prüfen. Das NAS-Repository wurde auf `58f9bce` synchronisiert; diese Dokumentationsdatei kommt als neue lokale Datei hinzu.
- Kein pauschales `reset --hard`, Löschen von Historie oder Überschreiben abweichender Nutzeränderungen zum „Entfernen der M“.
- Den aktuellen Stilllegungswunsch respektieren. Bei einem reinen Analyseauftrag keine geplanten oder manuellen Actions-Läufe und keine Pages-Veröffentlichung auslösen.
- Keine vollständigen Modulimporte ausführen, wenn Paketinstallation oder andere Nebenwirkungen unzulässig sind.
- Funktionsumfang und Datenquellen nachweisen, bevor Erfolg erklärt wird.

### K.3 Welche Entscheidungen zu erhalten sind

- Preis wichtiger als Airline; gemischte Airlines sind zulässig.
- Mindestens zwei Nächte; das zuletzt bekannte historische Fenster enthält sechs Paarungen.
- Statisches Datumsfenster ist gewollt, eine zusätzliche interaktive Konfiguration nicht.
- Die vorhandene HTML-Tabellenansicht wurde akzeptiert. Ein UI-Neubau ist nicht automatisch Teil einer Adapterkorrektur.
- Cloud-Ausführung statt Abhängigkeit vom eingeschalteten Mac war die gewählte Architektur.
- Pause und Erhalt des Codes sind die letzte Betriebsentscheidung.
- Gedachte Endpunkte, API-Abdeckungen oder vermutete Ursachen sind keine verifizierten Fakten.

### K.4 Besonders vorsichtige Änderungsbereiche

- **Provideradapter:** Echte Antwortschemata prüfen; Nicht-200, Nulltreffer und ungültige Daten unterscheiden. Keine weiteren geratenen Fallbacks als fertige Integration verkaufen.
- **Preisvergleich:** Tarifbedingungen und Reisendenkontext nicht stillschweigend ändern. Tagesminimum plus Tagesminimum ist das aktuelle Modell, nicht der Beweis eines global günstigsten buchbaren Rundreisepreises.
- **Historie:** Datenmodell und Suchkontext berücksichtigen. Vor Änderungen an der Persistenz ältere Tagesstände erhalten.
- **Template:** F-String-Klammern sowie Chart-Daten und feste Labels beachten. Produktive Änderungen in `generate_dashboard()` statt allein in `index.html` vornehmen.
- **Workflow/Pages:** Verhalten mit `GITHUB_TOKEN`, Defaultbranch und Pages-Einstellungen prüfen. Privates Repository nicht mit privater Website gleichsetzen.
- **NAS/Git:** Lokale `core.filemode=false`-Einstellung und lokale Exclude-Regeln sind bewusst gesetzt. Ein erneutes NAS-`FETCH_HEAD`-Problem ist kein Grund, beliebige `.git`-Dateien zu entfernen.

### K.5 Was vor einer Wiederaufnahme noch zu klären ist

Nur bei einem entsprechenden neuen Entwicklungsauftrag sind folgende Fragen offen:

- Neuer Reisezeitraum, da die bisherigen Daten vergangen sind.
- Ob die Suche wieder automatisch und ob eine Website wieder öffentlich laufen soll.
- Welcher Datenanbieter real zugänglich ist und die gewünschte Route/airlineübergreifende Suche abdeckt.
- Bei einer Aggregator-Integration: Reisendenzahl, gewünschtes Gepäck, Direktflug-/Umstiegsbedingungen und Umgang mit separaten Tickets; diese Kriterien wurden bisher nicht vollständig spezifiziert.
- Ob der Trend die bestehende 0,50-EUR-Toleranz behalten soll, falls dessen Semantik geändert wird.
- Gegebenenfalls gewünschte Uhrzeit beziehungsweise akzeptierte UTC-Ausführung.

Nicht erneut grundsätzlich fragen, ob Airline oder Preis wichtiger sind, ob zwei Nächte verlangt werden, ob ein zusätzliches Dashboard gewünscht ist oder ob ohne Anlass ein weiterer lokaler Projektordner angelegt werden soll: Diese Punkte sind bereits entschieden.

## L. Pflege, Nachweise und Grenzen dieser Übergabe

### L.1 Nachweise im Projekt

Die primären Belege sind der Quellcode und die mit Git verfolgten Dateien. Relevante externe Nachweise wurden an den jeweiligen Aussagen verlinkt: GitHub-Publishing, Workflow-Deaktivierung, Pages-Unpublish und offizielle Skyscanner-API-Dokumentation.

Die GitHub-Metadaten-/Logbeobachtungen stammen aus der Vorbereitung dieser Übergabe in derselben sichtbaren Unterhaltung. Sie ersetzen keine aktuelle Prüfung der Administrationsseiten. Die Vollständigkeit der Airline-Suche, der aktive Schedulerzustand und der heutige Pages-Zugriff bleiben ausdrücklich nicht verifiziert.

### L.2 Aktualisierung dieser Datei

Bei späteren Änderungen mindestens Folgendes nachführen:

- Dokumentationsdatum, Bezugscommit und aktiver Betriebswunsch.
- Reisefenster und Suchbedingungen.
- Tatsächlich erfolgreiche Quellen und deren Belege.
- Datenmodell, neue Dateien, Konfiguration und benötigte Variablennamen ohne geheime Werte.
- Verifizierte Start-/Test-/Deploymentbefehle und deren tatsächliche Ausführungsergebnisse.
- Erledigte beziehungsweise weiterhin offene Aufgaben.
- Unterschiede zwischen fachlicher Entscheidung, technischer Umsetzung und bloßer Empfehlung.

Historische Entscheidungen nicht ohne Grund löschen. Überholte Aussagen als ersetzt oder widerlegt markieren. Insbesondere die früher zu weitgehenden API- und Erfolgsaussagen dürfen bei einer Zusammenfassung nicht erneut zu vermeintlich gesicherten Fakten werden.

### L.3 Übergabegrenze

Mit dieser Datei kann ein neuer Assistent Architektur, Datenfluss, UI, GitHub-Betrieb, aktuelle Grenzen und die nachvollziehbaren Nutzerentscheidungen ohne erneutes Durcharbeiten des gesamten Threads verstehen. Für neue Live-Abfragen und einen Wiederbetrieb fehlen weiterhin ein neuer Reiseauftrag, ein validierter Weg zur airlineübergreifenden Abdeckung sowie die Prüfung der aktuellen Workflow-/Pages-Einstellungen. Diese Ungewissheiten sind bewusst erhalten und werden nicht durch Annahmen ersetzt.
