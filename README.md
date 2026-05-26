# Pool Pump Manager

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License](https://img.shields.io/github/license/Shad107/ha-pool_pump.svg)](LICENSE)

Custom Home Assistant integration that schedules a swimming-pool filtration
pump (and optionally a salt-water electrolyzer) based on a temperature input.

This fork is a clean rewrite of [oncleben31/ha-pool_pump][upstream] (last
release 2021, broken on Home Assistant 2025.11+ due to the removal of the
`homeassistant.core.Config` alias). It drops the `pypool_pump` external
dependency, adds a UI-based config flow, native entities, electrolyzer
support, and a forecast-aware heatwave override.

[upstream]: https://github.com/oncleben31/ha-pool_pump

## What it does

For each tick (every minute), the integration:

1. Reads a temperature sensor you provide (water temperature ideally; or a
   daily-mean air temperature as a defensible fallback).
2. Computes the daily run duration:
   - `duration = temperature / 2` (or `/3` below 13 °C),
   - clamped to `[min_hours, max_hours]`.
3. If an optional forecast sensor is configured and reads at or above the
   heatwave threshold, the duration is forced to `max_hours` (24 h by
   default). This is the forecast-aware override.
4. Centers the run on the **pivot hour** (default 14:00 local — solar peak).
   Optionally splits it into two with a midday break.
5. Drives the pump switch on/off based on the schedule, and if an
   electrolyzer switch is configured, drives it inside the same window with
   configurable post-start and pre-stop margins (typical: cell on 2 min
   after the pump starts, cell off 1 min before the pump stops).

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
- **Electrolyzer support** — optional switch with configurable ON/OFF margins.
- **Heatwave override** — optional forecast sensor + threshold.
- **Native entities** — sensors, binary sensors, a mode selector, all
  attached to a single device. Dashboards can target them directly.
- **Translations** — English and French shipped.

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

| Required | Field | Notes |
|---|---|---|
| ✓ | Pool pump switch | Any HA `switch.*` entity that powers the pump |
| ✓ | Temperature sensor | Water temp if you have a probe, else a daily-mean air temp template |
|   | Min / max hours | Clamp the computed duration (defaults 2 / 24) |
|   | Pivot hour | Centers the run; default 14 |
|   | Midday break (h) | If > 0, splits the run into two |
|   | Forecast sensor | Optional. Tomorrow's max temp; triggers heatwave override |
|   | Heatwave threshold | Default 28 °C |
|   | Electrolyzer switch | Optional |
|   | Electrolyzer post-start delay (s) | Default 120 |
|   | Electrolyzer pre-stop delay (s) | Default 60 |
|   | Low-water binary sensor | Optional. Blocks the pump if `on` |

Options can be edited later via *Settings → Devices & services → Pool Pump
Manager → Configure*.

## Entities created

- `select.pool_pump_manager_mode` — Auto / On / Off (manual override)
- `sensor.pool_pump_manager_pump_start_time` — next start (timestamp)
- `sensor.pool_pump_manager_pump_end_time` — next end (timestamp)
- `sensor.pool_pump_manager_pump_daily_duration` — total daily hours
- `sensor.pool_pump_manager_temperature_used` — temperature used in the math
- `sensor.pool_pump_manager_status` — current reason (`auto`, `off`,
  `heatwave`, `manual_on`, `manual_off`, `water_low`)
- `binary_sensor.pool_pump_manager_pump_should_be_on`
- `binary_sensor.pool_pump_manager_electrolyzer_should_be_on` (only if an
  electrolyzer is configured)
- `binary_sensor.pool_pump_manager_heatwave_override`

A single service is exposed:

- `pool_pump.refresh` — recompute and reapply immediately (used by the
  dashboard card).

## Dashboard card

A ready-to-paste Lovelace card template is included in
[`lovelace_card.yaml`](./lovelace_card.yaml). Copy its contents into a
Manual card on your dashboard, adjust entity IDs if needed, and you're set.

## Temperature input — pragmatic advice

The literature consensus for residential pools is `duration = T_water / 2`.
A real water-temp probe (a DS18B20 in the skimmer, ~25 €) is the
right input. Without a probe, a daily-mean air temperature is the
least-bad proxy — but it lags reality on heatwaves, which is precisely
what the forecast override is for.

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
