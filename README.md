# Pool Pump Manager

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License](https://img.shields.io/github/license/Shad107/ha-pool_pump.svg)](LICENSE)

Custom Home Assistant integration that schedules a swimming-pool filtration
pump (and optionally a salt-water electrolyzer) based on a temperature input,
with an optional air-based thermal model for installs without a water probe
and a curated catalog of common Intex / Bestway pool models.

This fork is a clean rewrite of [oncleben31/ha-pool_pump][upstream] (last
release 2021, broken on Home Assistant 2025.11+ due to the removal of the
`homeassistant.core.Config` alias). It drops the `pypool_pump` external
dependency, adds a UI-based config flow, native entities, electrolyzer
support with cell-protection cutoffs, a forecast-aware heatwave override,
a pool-model catalog, and a Lovelace dashboard card with a visual rendering
of the pool.

[upstream]: https://github.com/oncleben31/ha-pool_pump

## What it does

For each tick (every minute), the integration:

1. Determines the water temperature:
   - **Water sensor mode** — uses the configured sensor directly.
   - **Air-based model mode** — integrates a 1st-order thermal model
     (`dT_water/dt = (T_air + offset - T_water) / τ`) from the configured
     air temperature sensor. The modeled water temperature is persisted
     across HA restarts. `τ` is taken from the configured value, or
     derived from the selected pool model, or defaults to 36 h.
2. Computes the daily run duration:
   - `duration = temperature / 2` (or `/3` below 13 °C),
   - clamped to `[min_hours, max_hours]`.
3. If an optional forecast sensor reads at or above the heatwave threshold,
   the duration is forced to `max_hours` (24 h by default).
4. Centers the run on the **pivot hour** (default 14:00 local), optionally
   split into two with a midday break.
5. Drives the pump switch on/off. If an electrolyzer switch is configured,
   drives it inside the same window with post-start / pre-stop margins
   (defaults 120 s / 60 s — consistent with manufacturer flow-switch
   debounce times), AND blocks the cell when water temperature is outside
   `[15 °C, 40 °C]` (literature-backed cell protection, defaults adjustable).

## Why a fork

The upstream integration is unmaintained. Its breakage on HA 2025.11+ is
tracked at [oncleben31#36](https://github.com/oncleben31/ha-pool_pump/issues/36).
Reusing it required incompatible patches and a YAML-only setup. This fork
takes the algorithm idea (T-based duration centered on solar noon) and
ships it as a modern HA component.

## What changed vs upstream

- **Loads on HA 2026.5+** — no more `from homeassistant.core import Config`.
- **UI configuration** — `config_flow` + options flow, no `configuration.yaml`.
- **No external library** — `pypool_pump` removed, math inlined.
- **Air-based thermal model** — first-order RC with persistent state, for
  installs without a water temperature probe.
- **Pool model catalog** — 43 popular models (Intex, Bestway, generic
  in-ground) with known geometry; `τ` is derived from the selected model.
- **Electrolyzer support** — optional switch with configurable ON/OFF
  margins **and** water-temperature cutoffs (cell off below 15 °C / above
  40 °C by default, per manufacturer practice).
- **Heatwave override** — optional forecast sensor + threshold.
- **Native entities** — sensors, binary sensors, mode selector, all
  attached to a single device. Dashboards can target them directly.
- **Translations** — English and French shipped.
- **Lovelace card with visual** — the dashboard card renders an SVG of the
  pool shape (round / rectangular / oval) at the right proportions, with
  color reflecting the pump state.

## Install

### Via HACS (recommended)

1. HACS → Integrations → top-right menu → *Custom repositories*.
2. Add `https://github.com/Shad107/ha-pool_pump` as category *Integration*.
3. Search for **Pool Pump Manager** and install.
4. Restart Home Assistant.
5. *Settings → Devices & services → Add integration → Pool Pump Manager*.

### Manual

Copy `custom_components/pool_pump/` into your HA `config/custom_components/`
directory. Restart Home Assistant. Then add via the UI as above.

## Configuration

The setup wizard collects:

### Step 1 — required

| Field | Notes |
|---|---|
| **Pool pump switch** | Any HA `switch.*` entity that powers the pump |
| **Temperature mode** | Water sensor (probe) **or** Air-based model |
| **Temperature sensor** | Water probe if mode = water; air sensor otherwise |

### Step 2 — options

| Field | Default | Notes |
|---|---:|---|
| Pool model | Custom | Drives the dashboard visual and (in air mode) the default τ |
| Pool has cover | Off | Multiplies τ by 2.5 |
| τ (thermal time constant, hours) | derived | Blank = derive from pool model |
| Air → water offset (°C) | 0 | Bias applied in the air-based model |
| Min / max hours | 2 / 24 | Clamp on computed duration |
| Pivot hour | 14 | Centers the run, local time |
| Midday break (h) | 0 | If > 0, splits the run into two |
| Forecast sensor | — | Triggers heatwave override |
| Heatwave threshold (°C) | 28 | Forecast ≥ threshold → run max hours |
| Electrolyzer switch | — | Optional |
| Electrolyzer post-start (s) | 120 | Cell-ON delay after pump start |
| Electrolyzer pre-stop (s) | 60 | Cell-OFF lead time before pump stop |
| Electrolyzer min water temp (°C) | 15 | Cell off below — literature-backed |
| Electrolyzer max water temp (°C) | 40 | Cell off above — AstralPool guidance |
| Low-water binary sensor | — | If `on`, blocks the pump |

Options can be edited later via *Settings → Devices & services → Pool Pump
Manager → Configure*.

## Entities created

- `select.pool_pump_manager_mode` — Auto / On / Off
- `sensor.pool_pump_manager_pump_start_time`
- `sensor.pool_pump_manager_pump_end_time`
- `sensor.pool_pump_manager_pump_daily_duration`
- `sensor.pool_pump_manager_temperature_used`
- `sensor.pool_pump_manager_status` — `auto` / `off` / `heatwave` / `manual_on` / `manual_off` / `water_low`
- `sensor.pool_pump_manager_pool` — pool name; attributes include `shape`, `volume_m3`, `surface_m2`, `depth_m`, `manufacturer`, `svg`
- `binary_sensor.pool_pump_manager_pump_should_be_on`
- `binary_sensor.pool_pump_manager_electrolyzer_should_be_on` (if electrolyzer configured)
- `binary_sensor.pool_pump_manager_heatwave_override`

A single service is exposed:

- `pool_pump.refresh` — recompute and reapply immediately (used by the
  dashboard card).

## Dashboard card

A ready-to-paste Lovelace card template is included in
[`lovelace_card.yaml`](./lovelace_card.yaml). It uses a markdown card to
render the SVG attribute of `sensor.pool_pump_manager_pool` — the pool
shows up at the correct shape and proportions, with the color shifting
between idle (light blue), running (deep blue with ripple lines) and
forced-off (grey).

## Pool model catalog

The integration ships with 43 presets:

- **Intex** Easy Set, Metal Frame, Prism Frame, Rectangular Frame, Ultra
  XTR (round, rect, oval)
- **Bestway** Steel Pro, Steel Pro Max, Power Steel, Hydrium (round, rect,
  oval)
- **Generic** in-ground rectangular sizes (25, 40, 60, 90 m³) and round

Each preset stores volume, surface, depth, shape, and manufacturer. When a
preset is selected, the thermal time constant `τ` is computed empirically
as `depth_m × exposure_factor × cover_factor × 20` hours, where exposure
is 0.8 for aboveground frame pools (wind-exposed, conductive walls) and
1.2 for in-ground (sheltered, lossy through soil), and cover doubles τ
(set the "has cover" toggle to apply).

This is a heuristic. Use it as a starting point, observe how the modeled
water temperature compares to actual feel over 1–2 weeks, and override
`τ` manually if needed.

## Temperature input — pragmatic advice

The literature consensus for residential pools is `duration = T_water / 2`.
A real water-temp probe (a DS18B20 in the skimmer, ~25 €) is the right
input. Without a probe, the air-based model is the next-best option: it
filters the diurnal air-temperature swing through the pool's thermal
inertia and gives a defensible water proxy. The forecast override
compensates for the air-based model's lag during heatwaves.

## Electrolyzer timing — what the literature says

Major manufacturers (Hayward, Pentair, Zodiac, AstralPool, Bayrol, Sugar
Valley) all rely on a flow switch as the primary safety. The
post-start / pre-stop offset is a belt-and-suspenders layer that:

- gives the pump time to purge air and stabilize flow before energizing
  the cell (dry-firing destroys the titanium coating in seconds),
- flushes the cell with a chlorine-free water bolus before pump-off,
  protecting nearby metal from corrosion and avoiding hydrogen pocketing.

Defaults of 120 s / 60 s are squarely in manufacturer-consensus ranges
(Hayward's internal debounce is 60 s; field techs commonly cite "2 min
on, 1 min off" verbally).

Low-temp cutoff defaults (15 °C) align with Bayrol AS5/AS7 and most EU
brands; high-temp cutoff (40 °C) follows AstralPool VX guidance.

## Migrating from upstream

If you came from `oncleben31/ha-pool_pump`:

1. Remove `pool_pump:` from `configuration.yaml`.
2. Delete the legacy helper entities and automations:
   - `input_select.pool_pump_mode`
   - `input_number.run_pool_pump_hours_*`
   - The four `Pool Manager - …` automations
3. Restart HA.
4. Install this fork and configure via UI.

## License

MIT — see [LICENSE](LICENSE).
