# Pool Pump Manager (Shad107 fork)

Modern rewrite of the abandoned `oncleben31/ha-pool_pump`. Works on
Home Assistant 2026.5+, sets up via UI, supports an electrolyzer and a
forecast-aware heatwave override.

## Features

- UI configuration (no YAML)
- Daily run duration computed from a temperature input (`T/2`, `T/3`
  below 13 °C), clamped, centered on a pivot hour with optional midday
  break
- Optional forecast sensor → forces max hours during heatwaves
- Optional electrolyzer switch with configurable post-start and pre-stop
  margins
- Optional low-water binary sensor blocks the pump when triggered
- Native entities (sensors, binary sensors, mode selector) attached to a
  single device
- English and French translations included
- A ready-to-paste Lovelace dashboard card template ships with the repo

See the [README](https://github.com/Shad107/ha-pool_pump#readme) for full
details and migration notes from upstream.
