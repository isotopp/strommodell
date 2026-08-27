# Datenquellenprüfung: Deutschland 2024

**Entscheidung:** Als Rohquelle verwenden wir den öffentlichen Endpunkt von
Fraunhofer ISE Energy-Charts:

```text
https://api.energy-charts.info/public_power?country=de&start=2024-01-01&end=2024-12-31
```

Die versionierte Rohdatei und ihre Metadaten liegen unter `data/raw/`. Die Datei
ist ein JSON-Dokument mit einer gemeinsamen
`unix_seconds`-Achse und parallel ausgerichteten Reihen je Erzeugungsart.

## Testdownload und Qualitätsprüfung

Abruf am 2026-08-27T09:10:37Z, SHA-256:
`54d5e2e74bf980c4b4334aef3aeeb4dd2d39c7747795444b18bdd58c7e2385cd`.

| Prüfung | Ergebnis |
| --- | ---: |
| Zeitraum (UTC) | 2023-12-31 23:00 bis 2024-12-31 22:45 |
| Messpunkte | 35.136 = 366 × 96 |
| Schrittweite | lückenlos 900 Sekunden |
| fehlende Werte: Last, PV, Wind Land, Wind See | jeweils 0 |
| integrierte Last | 465,503 TWh |
| PV / Wind Land / Wind See | 59,707 / 110,642 / 25,682 TWh |
| zeitlicher Mittelwert EE-Anteil Last / Erzeugung | 55,90 % / 61,21 % |

Die Last-Jahresarbeit stimmt mit den im Grundlagenartikel genannten 465,5 TWh
überein. Die Werte sind Leistung in MW; die obige Arbeit entsteht durch
Integration mit 0,25 Stunden je Messpunkt.

Die beiden gelieferten EE-Anteile sind Momentanwerte. Ihr zeitlicher
Mittelwert ist **nicht** automatisch ein energiegewichteter Jahresanteil und
ist deshalb nur eine Plausibilitätskennzahl.

## Stündliche Modellreihe

Die Quelle ist viertelstündlich, was für Batterie-Leistung besser ist als die
geforderte Stundenreihe. Story 2 erzeugt daraus eine stündliche Anzeige- und
Importvariante durch Mittelwertbildung über vier vollständige Viertelstunden.
Die Rohreihe bleibt erhalten; sie vermeidet eine irreversible zeitliche
Glättung und kann später direkt für Batterie-Dispatch genutzt werden.

Für die Modellinputs sind ausschließlich `Load`, `Solar`, `Wind onshore` und
`Wind offshore` relevant. `Renewable share of load` und `Renewable share of
generation` sind nützliche Plausibilitätsreihen, aber kein Recheninput.

## Offener Datenpunkt: Referenzleistung

Der ebenfalls getestete Endpunkt
`https://api.energy-charts.info/installed_power?country=de&start=2024-01-01&end=2024-01-02`
liefert installierte Leistung lediglich jährlich (Stichtag 31.12.), nicht pro
Viertelstunde. Er eignet sich deshalb für Szenario 0 am Jahresende, aber nicht
für die in Story 3 geforderte zeitlich passende Referenzleistung. Dafür muss
eine zweite Quelle mit Inbetriebnahme-/Monatsdaten ergänzt oder die Story für
den ersten Lauf ausdrücklich auf einen festen Referenzbestand einschränkt
werden.
