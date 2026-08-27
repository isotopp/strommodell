# Verbindliche Modellentscheidungen

Diese Entscheidungen konkretisieren den Artikel und die User Stories. Sie
gelten für den ersten implementierten Modellstand und werden als Annahmen in
jeden Ergebnisbericht geschrieben.

## Zeit und Daten

- **Datenjahr 2024:** Der Energy-Charts-Rohdownload ist die kanonische Quelle.
  Intern bleiben Zeitstempel UTC und der Dispatch läuft mit 15 Minuten. Eine
  stündliche Ansicht entsteht durch Mittelwert über vier vollständige Werte.
- **Last:** `Load` wird proportional auf 1.100 TWh skaliert. Es gibt weder eine
  versteckte 200-GW-Obergrenze noch eine künstliche Lastform; Jahresarbeit,
  Mittelwert und Spitze werden berichtet.
- **Erzeugungsprofil:** Verwendet werden `Solar`, `Wind onshore` und `Wind
  offshore`. Das beobachtete Profil enthält damit auch historische
  Abregelungs- und Netzrestriktionseffekte. Es wird vorerst nicht zu einem
  hypothetisch unbeschränkten Wetterprofil korrigiert.

## Referenz- und Szenarioleistung

Die Quelle liefert nur Jahresendstände. Für ein Datenjahr `y` definieren wir
die Referenzleistung jeder Technologie als:

```text
(Bestand zum 31.12.(y-1) + Bestand zum 31.12.y) / 2
```

Das ist ein Jahresmittel und bewusst **keine** Behauptung einer zeitvariablen
Kapazitätsreihe. Für 2024 ergeben sich aus dem versionierten Energy-Charts-
Schnappschuss:

| Technologie | Ende 2023 | Ende 2024 | Referenz 2024 |
| --- | ---: | ---: | ---: |
| PV (DC/GWp) | 83,300 GW | 100,787 GW | 92,044 GW |
| Wind an Land | 61,013 GW | 63,589 GW | 62,301 GW |
| Wind auf See | 8,473 GW | 9,215 GW | 8,844 GW |

PV-Leistungen werden ausdrücklich als **DC/GWp** behandelt, passend zur
`Solar DC`-Reihe der Kapazitätsquelle. Die Leistungsreihe `Solar` beschreibt
die beobachtete Einspeisung; ihre Division durch DC/GWp ist der verwendete
empirische Kapazitätsfaktor. Alle PV-Szenariowerte sind daher ebenfalls
DC/GWp. Windwerte sind GW.

Die Skalierung bleibt technologiegetrennt:

```text
Szenarioerzeugung(t) = beobachtete Erzeugung(t) / Referenzleistung * Szenarioleistung
```

Die Szenario-0-Werte aus dem Artikel bleiben als bewusst benannte
**End-2024-Bestandsannahme** erhalten; für die Skalierung des Profils wird
hingegen stets die obige Referenz 2024 verwendet.

## Batterie und Restdeckung

- Ein Lauf beginnt mit **50 %** des nutzbaren Batterieenergieinhalts. Der
  Anfangswert ist damit `0,5 * Leistung_GW * Dauer_h`.
- Es gibt im ersten Modell keine End-SOC-Nebenbedingung und keine
  Jahresverknüpfung. Der End-SOC wird berichtet. Jeder Wetterjahreslauf startet
  erneut mit 50 %.
- Batterieenergie ist `Leistung × Dauer`; als Default gelten vier Stunden,
  je 90 % Lade- und Entladewirkungsgrad sowie getrennte Leistungsgrenzen in
  beide Richtungen.
- Überschuss lädt zuerst die Batterie, dann wird abgeregelt. Defizit entlädt
  zuerst die Batterie, dann deckt Gas die elektrische Restleistung vollständig.
- Gas ist ausschließlich elektrische Versicherungskapazität. Es gibt weder
  Importe/Exporte noch unversorgte Last, Brennstoffmengen oder Gaswirkungsgrad.

## Reproduzierbarkeit und Fehlerverhalten

- Fehlende Werte, unregelmäßige Zeitabstände, fehlende Technologie oder eine
  null/negative Referenzleistung brechen den Lauf mit einer Datenfehlermeldung
  ab.
- Berichte enthalten immer Datenjahr, Datei-Prüfsummen, Datenauflösung,
  Kapazitätsregel, Batterieannahmen und alle Szenariowerte.
