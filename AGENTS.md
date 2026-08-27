# Strommodell – Arbeitsregeln

Das Projekt ist ein reproduzierbares Python-Package für historische deutsche
Stromzeitreihen und Szenarien eines elektrifizierten Deutschlands.

## Entwicklungsablauf

- Implementiere die Stories im jeweiligen Epic-Verzeichnis als vertikale
  TDD-Slices: ein Verhaltenstest über die öffentliche API oder CLI, dann die
  kleinste passende Implementierung.
- Tests prüfen keine privaten Hilfsfunktionen. Echte Netzabrufe bleiben
  separat markiert; Standardtests verwenden kleine, eingecheckte Fixtures.
- Verwende explizite Einheiten im Namen und in Typen (`*_gw`, `*_gwh`,
  `*_twh`). Zeitstempel werden intern in UTC geführt.
- Skaliere jede Technologie mit der zum Zeitschritt passenden
  Referenzleistung. Fehlende oder null Referenzwerte sind Datenfehler.

## Qualitätsgates

Vor der Übergabe immer ausführen:

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

## Daten und Ergebnisse

- Der kanonische Rohdownload in `data/raw/` wird mit Herkunft und Prüfsumme
  versioniert; große abgeleitete Referenzdaten bleiben unter `data/reference/`
  lokal.
- Kleine Testdaten gehören nach `tests/fixtures/` und werden eingecheckt.
- Generierte Läufe gehören nach `results/` und werden nicht eingecheckt.
