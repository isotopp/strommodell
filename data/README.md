# Lokale Modelldaten

Der kanonische Rohdownload in `raw/` wird zusammen mit seiner Metadatendatei
versioniert. Diese enthält URL, Abrufzeitpunkt (UTC), Datenjahr, Zeitzone,
Auflösung, Einheiten und SHA-256-Prüfsumme. Große abgeleitete Referenzdaten
bleiben lokal unter `reference/`.

`tests/fixtures/` enthält dagegen kleine, versionierte Testdaten. Ergebnisse
von Szenarioläufen gehören nach `results/`.
