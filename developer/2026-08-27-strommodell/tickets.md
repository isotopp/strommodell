# Implementation Tickets: Strommodell

## Rules for every ticket

- Work on one ticket only. Begin with its named public behavior test, observe
  RED, implement only enough to reach GREEN, then run all quality gates.
- Use only public Python APIs or the installed `strommodell` CLI in tests.
  Keep network access out of the default test suite.
- Follow `model-decisions.md` where it narrows or corrects a user story.
- Commit a completed ticket with the `git-commit` skill before starting the
  next one.

## T-001 — Complete the executable package baseline

**Story:** 0
**Status:** complete in `e9bb761`.

The installable package, quality tools and the `download`, `run`, `report`
help entries already exist. Keep the CLI behavior test as the regression gate.

**Public behavior test:** `strommodell --help` exits successfully and lists
`run`.

## T-002 — Reproduce the checked-in Energy-Charts raw snapshot

**Story:** 1
**Depends on:** T-001

Create one public local import API that copies the existing
`data/raw/energy-charts-public-power-de-2024.json` snapshot into a caller-
selected directory and regenerates its provenance metadata. The canonical
Energy-Charts JSON itself is the golden fixture: it contains the shared UTC
timestamp axis and the four required series without any network call. The
metadata must retain the JSON source format, URL, year, timezone, resolution,
units, sample count, required series and SHA-256.

**Public behavior test:** import the checked-in snapshot into a temporary output
directory; assert byte-identical raw JSON and metadata with a valid UTC
retrieval timestamp, source URL, year, timezone, resolution, units and digest.

**Done when:** malformed or incomplete Energy-Charts JSON produces an
understandable public data error; the default test suite has no network
dependency.

## T-003 — Implement the Energy-Charts download command

**Story:** 1
**Depends on:** T-002

Implement `strommodell download --year 2024 --source energy-charts`. Fetch the
official `public_power` JSON endpoint, pass the response through the T-002
import boundary, and write the same raw filename and metadata shape as the
checked-in snapshot. Add a separately marked network test only; ordinary tests
use a local HTTP-free fake or fixture.

**Public behavior test:** invoke the command against a fixture-backed download
transport and assert the documented raw filename and metadata fields.

**Done when:** an existing download is either reused only after checksum and
metadata validation, or rejected with a clear error; no silent overwrite is
allowed.

## T-004 — Normalize and validate a reference year

**Story:** 2
**Depends on:** T-002

Implement `load_reference_year(path, year=2024)`. Map the four Energy-Charts
series to UTC observations in GW, retain a 15-minute step, and attach the
annual-average reference capacities specified in `model-decisions.md`.
Validate aligned lengths, unique timestamps, fixed spacing, required series,
numeric values and positive reference capacity. Expose integration of power
over the actual step duration.

**Public behavior test:** load two hourly 1-GW observations and obtain 2 GWh;
also prove that four 15-minute 1-GW observations integrate to 1 GWh.

**Done when:** missing, duplicate or irregular timestamps fail with a helpful
exception; a separate public conversion provides hourly mean-power views
without discarding the canonical 15-minute data.

## T-005 — Scale PV and wind generation

**Story:** 3
**Depends on:** T-004

Implement `scale_generation(reference, pv_gw, wind_onshore_gw,
wind_offshore_gw)` using the fixed annual-average reference capacity for the
data year. Treat PV values as DC/GWp and wind as GW. Scale each technology
independently and leave the observed profile otherwise unchanged.

**Public behavior test:** 3 GW PV with 10 GW reference and 40 GW scenario PV
becomes 12 GW; invalid reference capacity fails instead of dividing.

**Done when:** the result carries units and timestamps unchanged and reports no
combined, technology-mixing capacity factor.

## T-006 — Scale the electrical demand profile

**Story:** 4
**Depends on:** T-004

Implement `scale_demand(reference.load_gw, annual_twh=1100)`. Preserve all
relative load values while scaling total integrated work to the requested
annual target. Make mean and observed peak available to callers and reports;
do not cap the result at 200 GW.

**Public behavior test:** a small load profile reaches exactly its requested
work while every pairwise load ratio remains unchanged.

**Done when:** zero or negative input work is rejected as a data error.

## T-007 — Dispatch the four-hour battery

**Story:** 5
**Depends on:** T-004

Implement `dispatch_battery` over 15-minute residual-load observations. Default
to four hours duration, 90% charge efficiency and 90% discharge efficiency.
When a scenario does not explicitly override it, initialize state of charge to
50% of usable energy. Return state of charge, charge/discharge, curtailment,
remaining positive residual load, throughput and final state of charge.

**Public behavior test:** a constant surplus fills a four-hour empty battery
only to its energy capacity and reports later surplus as curtailment.

**Done when:** every time step observes charge/discharge power bounds and
`0 <= state_of_charge <= energy_capacity`; efficiencies are accounted for in
energy, not silently folded into power.

## T-008 — Run a fully covered gas-residual scenario

**Story:** 6
**Depends on:** T-005, T-006, T-007

Implement `run_scenario(reference, scenario)`. Construct scaled generation and
demand, dispatch the battery, and set gas power to the remaining positive
residual load. Calculate gas peak and integrated gas work in electrical units.

**Public behavior test:** 50 GW remaining residual load for two hours produces
50 GW gas capacity and 100 GWh gas work.

**Done when:** the result explicitly records zero unserved load, no imports or
exports, and no gas fuel or efficiency calculation.

## T-009 — Parse scenarios and execute the run CLI

**Story:** 7
**Depends on:** T-008

Define the documented YAML schema for data year, source identity and scenarios
0/A/B/C. Implement `strommodell run scenarios/2024.yaml --output results/2024`
to validate it and write an individually reproducible result per scenario.
Use the article's end-2024 capacities for scenario 0 and its A/B/C values;
use the annual-average capacities only for profile scaling.

**Public behavior test:** invoke the CLI with a small fixture configuration and
assert that it writes a result directory with the scenario identifier and
provenance.

**Done when:** invalid units, missing fields and duplicate scenario names cause
clear CLI errors; result files include input checksums and assumptions.

## T-010 — Produce comparable Markdown and machine-readable reports

**Story:** 7
**Depends on:** T-009

Implement `strommodell report results/2024`. Produce a Markdown table plus CSV
or JSON containing capacities, battery power/energy, gas power/work,
curtailment, battery throughput, final state of charge and demand peak.
Include data year, source, resolution, capacity rule and efficiencies.

**Public behavior test:** report a fixture run and assert that the Markdown
table contains gas capacity and gas work.

**Done when:** machine-readable output uses unambiguous GW/GWh/TWh field names
and scenario rows can be compared without reading the Markdown.

## T-011 — Add multi-year execution and critical-year reporting

**Story:** 8
**Depends on:** T-009, T-010

Extend the run CLI with `--years 2015:2024`. Keep each year independently
reproducible, initialize every year at 50% battery state of charge, and report
mean and maximum gas power/work and curtailment across years along with the
critical year.

**Public behavior test:** run two mini-years and identify the one with higher
gas capacity as critical.

**Done when:** a missing year fails explicitly rather than silently reducing
the requested range.
