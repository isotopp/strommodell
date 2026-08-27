# User Stories: Stromsystem-Modell Deutschland

## Ziel und Modellgrenzen

Wir modellieren ein elektrifiziertes Deutschland mit 1.100 TWh Jahresverbrauch.
Die zeitliche Grundlage sind historische deutsche Viertelstunden- oder Stundenreihen für Last, Photovoltaik, Wind an Land und Wind auf See.
Wind und PV werden auf eine Szenarioleistung skaliert; Batterien haben eine festgelegte Leistung und vier Stunden Energieinhalt.
Gaskraftwerke liefern ausschließlich die verbleibende Residuallast.
Im ersten Modell gibt es keine Importe, keine nicht gedeckte Last und keinen saisonalen Wasserstoffspeicher.

Die Stories sind vertikale TDD-Slices: Jede Story wird mit genau einem Verhaltenstest begonnen, minimal implementiert und erst bei Grün erweitert.
Tests prüfen ausschließlich die öffentliche Python-API oder die CLI, nie interne Hilfsfunktionen.

## Gemeinsame Begriffe

- **Referenzleistung**: Installierte Leistung der historischen Anlagen im jeweiligen Zeitschritt.
- **Szenarioleistung**: Im Modell angenommene installierte Leistung.
- **Kapazitätsfaktor**: `Erzeugung / Referenzleistung`; dimensionslos und für jeden Zeitschritt getrennt.
- **Residuallast**: Last minus Wind- und PV-Erzeugung.
- **Batterieleistung**: Maximale Lade- oder Entladeleistung in GW.
- **Batterieenergie**: Nutzbarer Energieinhalt in GWh; bei vier Stunden `4 * Batterieleistung`.
- **Gasarbeit**: Von Gaskraftwerken gelieferte elektrische Arbeit in TWh.
- **Gasleistung**: Höchste im Modell benötigte elektrische Gasleistung in GW.

## Story 0 – Ausführbares Projektgerüst

Als Modellierer möchte ich ein installierbares Python-Package mit einer klaren CLI haben, damit jede Rechnung reproduzierbar ausgeführt werden kann.

**Öffentliche Schnittstelle**

```bash
uv run strommodell --help
```

**Akzeptanzkriterien**

- `uv init --package` erzeugt das Paketgerüst in einem eigenen Verzeichnis.
- `uv run ruff format`, `uv run ruff check --fix`, `uv run ty check` und `uv run pytest` laufen erfolgreich.
- Die CLI zeigt Unterbefehle für `download`, `run` und `report`.

**Erster TDD-Zyklus**

Ein CLI-Test ruft `strommodell --help` auf und erwartet Exit-Code 0 sowie den Unterbefehl `run`.

## Story 1 – Referenzdaten lokal und nachvollziehbar ablegen

Als Modellierer möchte ich eine benannte historische Datenreihe lokal ablegen und ihre Herkunft dokumentieren, damit ein Modelllauf später mit genau denselben Eingangsdaten wiederholt werden kann.

**Öffentliche Schnittstelle**

```bash
uv run strommodell download --year 2024 --source energy-charts
```

**Akzeptanzkriterien**

- Der Download legt Rohdaten und eine kleine Metadatendatei ab: URL, Abrufzeitpunkt, Jahr, Zeitzone, Auflösung, Einheiten und Prüfsumme.
- Die Daten enthalten Last, PV, Wind an Land und Wind auf See.
- Der Download wird nicht in Unit-Tests benötigt; Tests verwenden eine mitgelieferte, kleine CSV-Fixture.
- Ein echter Downloadtest ist separat markiert und nur auf ausdrückliche Anforderung Teil der Testausführung.

**Erster TDD-Zyklus**

Ein Test übergibt eine lokale CSV-Fixture an die öffentliche Import-Schnittstelle und erwartet Rohdaten plus Metadaten im Zielverzeichnis.

## Story 2 – Zeitreihe normalisieren und prüfen

Als Modellierer möchte ich aus den Rohdaten eine einheitliche Zeitreihe erhalten, damit Last und Erzeugung zeitschrittgenau verrechnet werden können.

**Öffentliche Schnittstelle**

```python
reference = load_reference_year(path, year=2024)
```

**Akzeptanzkriterien**

- Jeder Zeitschritt hat einen eindeutigen UTC-Zeitstempel, Last in GW und Erzeugung in GW.
- Fehlende, doppelte oder unregelmäßig lange Zeitintervalle führen zu einer verständlichen Fehlermeldung.
- Die Umrechnung von Leistung zu Energie berücksichtigt die Schrittweite; eine Stundenreihe und eine Viertelstundenreihe ergeben für identische Werte dieselbe Arbeit.
- Die Referenzdaten enthalten die zeitlich passende installierte Leistung oder eine klar dokumentierte konstante Referenzleistung.

**Erster TDD-Zyklus**

Ein Test lädt zwei Stunden mit 1 GW Last und erwartet 2 GWh Jahresarbeit.

## Story 3 – Wind und PV korrekt auf Szenarioleistung skalieren

Als Modellierer möchte ich historische Wetter- und Erzeugungsprofile auf andere installierte Leistungen übertragen, damit Szenarien ohne erfundene Wetterdaten verglichen werden können.

**Öffentliche Schnittstelle**

```python
generation = scale_generation(
    reference, pv_gw=400, wind_onshore_gw=300, wind_offshore_gw=80
)
```

**Akzeptanzkriterien**

- Für jeden Zeitschritt gilt getrennt nach Technologie:

  ```text
  Szenarioerzeugung(t) = historische Erzeugung(t) / Referenzleistung(t) * Szenarioleistung
  ```

- Die Referenzleistung ist die Leistung im jeweiligen Zeitschritt, nicht blind der Bestand am Jahresende. Zubau im Laufe des Jahres verfälscht sonst den Kapazitätsfaktor.
- Ein fehlender oder nuller Referenzwert wird nicht stillschweigend durch Division ersetzt, sondern als Datenfehler gemeldet.
- PV, Wind an Land und Wind auf See sind getrennt skalierbar.

**Erster TDD-Zyklus**

Ein Test mit 10 GW Referenz-PV, 3 GW historischer PV-Erzeugung und 40 GW Szenario-PV erwartet 12 GW Szenarioerzeugung.

## Story 4 – Elektrifizierte Last erzeugen

Als Modellierer möchte ich die Referenzlast auf einen Jahresverbrauch von 1.100 TWh normieren, damit die Szenarien den im Artikel verwendeten Energiebedarf bedienen.

**Öffentliche Schnittstelle**

```python
load = scale_demand(reference.load_gw, annual_twh=1100)
```

**Akzeptanzkriterien**

- Die Summe über alle Zeitschritte beträgt 1.100 TWh innerhalb einer dokumentierten Rundungstoleranz.
- Die Form des historischen Lastprofils bleibt in diesem ersten Modell erhalten.
- Mittelwert und beobachtete Spitzenlast werden ausgegeben; die angenommene 200-GW-Spitze ist ein Vergleichswert, keine verdeckte Begrenzung.

**Erster TDD-Zyklus**

Ein Test skaliert eine kleine Lastreihe und erwartet exakt die vorgegebene Jahresarbeit bei unveränderten relativen Lastanteilen.

## Story 5 – Batterie mit vier Stunden Dispatch

Als Modellierer möchte ich Überschüsse zwischenspeichern und Defizite aus der Batterie decken, damit der Effekt von Kurzfristspeichern sichtbar wird.

**Öffentliche Schnittstelle**

```python
result = dispatch_battery(
    residual_load, power_gw=100, duration_hours=4, initial_soc_gwh=0
)
```

**Akzeptanzkriterien**

- Der Energieinhalt beträgt `power_gw * duration_hours`, im Referenzszenario also 400 GWh bei 100 GW und vier Stunden.
- Laden und Entladen sind jeweils durch die Batterie-Leistung begrenzt.
- Der Ladezustand bleibt immer zwischen 0 und Energieinhalt.
- Lade- und Entladewirkungsgrad sind als Parameter sichtbar und stehen im ersten Modell beide auf 90 Prozent.
- Überschüsse laden zuerst die Batterie; nur der Rest wird abgeregelt.
- Defizite werden zuerst aus der Batterie gedeckt; nur der Rest geht an Gas.

**Erster TDD-Zyklus**

Ein Test mit vier Stunden konstantem Überschuss lädt eine leere Vier-Stunden-Batterie genau bis zu ihrem Energieinhalt und weist den verbleibenden Überschuss als Abregelung aus.

## Story 6 – Gas als gesicherte Restleistung rechnen

Als Modellierer möchte ich die nach Batterie verbleibende Residuallast vollständig durch Gas decken, damit die notwendige Versicherungskapazität und ihre Jahresarbeit getrennt sichtbar werden.

**Öffentliche Schnittstelle**

```python
result = run_scenario(reference, scenario)
```

**Akzeptanzkriterien**

- Gasleistung ist das Maximum der nach Batterie verbleibenden positiven Residuallast.
- Gasarbeit ist die zeitliche Summe dieser Leistung.
- Nicht gedeckte Last ist in diesem Modell immer null; andernfalls schlägt der Lauf fehl.
- Die Berechnung nimmt weder Import noch Export an.

**Erster TDD-Zyklus**

Ein Test mit einer 50-GW-Restlast über zwei Stunden erwartet 50 GW Gasleistung und 100 GWh Gasarbeit.

## Story 7 – Szenarien vergleichbar berichten

Als Leser möchte ich die Szenarien in einer kompakten Tabelle vergleichen, damit Ausbau, Abregelung, Batterie und Gas nicht verwechselt werden.

**Öffentliche Schnittstelle**

```bash
uv run strommodell run scenarios/2024.yaml --output results/2024
uv run strommodell report results/2024
```

**Akzeptanzkriterien**

- Der Bericht enthält je Szenario PV, Wind an Land, Wind auf See, Batterie-Leistung/-Energie, Gasleistung, Gasarbeit, Abregelung, Batteriedurchsatz und Spitzenlast.
- Der Bericht nennt Datenjahr, Datenquelle, Auflösung und Annahmen zu Wirkungsgraden.
- Szenario 0 bildet den Anlagenbestand Ende 2024 ab; A, B und C entsprechen den Größenordnungen des Artikels.
- Die Ausgabe ist sowohl menschenlesbar als Markdown als auch maschinenlesbar als CSV oder JSON verfügbar.

**Erster TDD-Zyklus**

Ein Test führt einen Lauf mit einer kleinen Fixture durch und erwartet eine Markdown-Tabelle, die Gasleistung und Gasarbeit enthält.

## Story 8 – Wetterjahre und Sensitivitäten erweitern

Als Modellierer möchte ich identische Szenarien über mehrere historische Jahre ausführen, damit ich nicht zufällig ein windreiches oder mildes Jahr optimiere.

**Öffentliche Schnittstelle**

```bash
uv run strommodell run scenarios/2024.yaml --years 2015:2024 --output results/multiyear
```

**Akzeptanzkriterien**

- Jeder Jahreslauf bleibt einzeln nachvollziehbar.
- Der Bericht weist Maximum und Mittelwert der Gasleistung, Gasarbeit und Abregelung über alle Jahre aus.
- Das kritischste Jahr wird benannt, nicht in einem Mittelwert versteckt.

**Erster TDD-Zyklus**

Ein Test mit zwei Mini-Jahren erwartet, dass das Jahr mit der höheren Gasleistung als kritisches Jahr berichtet wird.

## Festgelegt vor Story 0

- Das Package liegt im separaten, leeren Git-Repository `strommodell`.
- Viertelstundenwerte sind die kanonische Modellauflösung; stündliche Werte
  werden nur als abgeleitete Ansicht erzeugt.
- Energy-Charts liefert die Leistung zum Jahresende. Für ein Datenjahr wird
  daher der Mittelwert aus Bestand am Jahresende des Vorjahres und des
  Datenjahres als Referenzleistung verwendet.
- PV-Leistungen sind DC/GWp; Windleistungen sind GW.
- Batterien starten jeden Jahreslauf bei 50 % ihres Energieinhalts.
- Gas wird ausschließlich als elektrische Restarbeit und -leistung gerechnet.
  Es gibt im ersten Modell keinen Brennstoff- oder Wirkungsgradpfad.
- Die vollständige Begründung, Zahlenwerte und Fehlerregeln stehen in
  `developer/2026-08-27-strommodell/model-decisions.md`.
