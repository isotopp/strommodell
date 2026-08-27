## Strommodell

Reproduzierbares Modell für historische deutsche Stromzeitreihen und Szenarien
eines elektrifizierten Deutschlands. Die fachlichen Anforderungen und
Modellentscheidungen stehen in
[`developer/2026-08-27-strommodell/user-stories.md`](developer/2026-08-27-strommodell/user-stories.md)
und
[`developer/2026-08-27-strommodell/model-decisions.md`](developer/2026-08-27-strommodell/model-decisions.md).

### Installation und Qualitätssicherung

Das Projekt verwendet [uv](https://docs.astral.sh/uv/). Abhängigkeiten und die
virtuelle Umgebung werden mit `uv sync` eingerichtet:

```bash
uv sync
uv run strommodell --help
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

### Daten und Szenarien

Die versionierten Energy-Charts-Rohdaten liegen in `data/raw`. Ein neuer
Download (inklusive Prüfsummen-Metadaten) wird so angelegt:

```bash
uv run strommodell download \
  --year 2024 \
  --source energy-charts \
  --output data/raw
```

Ein Szenario-Konfigurationsfile enthält das Datenjahr, die Rohdatenpfade und
eine Liste mit Szenarioleistungen. Der mitgelieferte Lauf verwendet die
historischen 2024er Profile und die Szenarien 0, A, B und C aus dem Artikel:

```bash
uv run strommodell run scenarios/2024.yaml --output results/2024
uv run strommodell report results/2024
```

Der Lauf schreibt pro Szenario eine JSON-Datei sowie `manifest.json`; der
Report besteht aus `report.md` und `report.csv`. Das Verzeichnis `results/` ist
bewusst in `.gitignore` eingetragen, damit reproduzierbare Ergebnisse lokal
erzeugt werden können, ohne große Artefakte zu versionieren.

### Modellannahmen des ersten Laufs

- Intern bleiben die Energy-Charts-Zeitstempel in UTC und die Rechnung läuft
  auf der kanonischen 15-Minuten-Auflösung. Eine Stundenansicht wird nur als
  Mittelwert aus vier vollständigen Viertelstunden abgeleitet.
- Die Last wird proportional auf 1.100 TWh Jahresarbeit skaliert; Mittelwert
  und beobachtete Spitze werden berichtet.
- Für PV und Wind wird das beobachtete Profil je Technologie mit
  `Szenarioleistung / Referenzleistung` skaliert. Da Energy-Charts nur
  Jahresendstände liefert, ist die Referenzleistung der Mittelwert aus dem
  Bestand zum 31.12. des Vorjahres und zum 31.12. des Datenjahres.
- PV-Leistungen sind DC/GWp, Wind-Leistungen GW. Abregelungseffekte der
  historischen Profile bleiben erhalten.
- Batterien haben standardmäßig vier Stunden Energieinhalt, 90 % Lade- und
  90 % Entladewirkungsgrad und starten bei 50 % Ladezustand. Überschüsse laden
  zuerst die Batterie; danach wird abgeregelt. Defizite werden zuerst aus der
  Batterie und anschließend vollständig durch elektrische Gasleistung gedeckt.
- Das erste Modell kennt keine Importe, Exporte, unversorgte Last oder
  Brennstoff-/Gaswirkungsgradrechnung. Die Mehrjahres-Sensitivität (T-011) ist
  für einen späteren Schritt zurückgestellt.
