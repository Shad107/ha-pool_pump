# Pool Pump Manager (Shad107 fork)

Modern rewrite of the abandoned `oncleben31/ha-pool_pump`. Works on
Home Assistant 2026.5+, sets up via UI, supports an electrolyzer with
literature-backed cutoffs, an air-based thermal model for installs without
a water probe, a curated catalog of 43 Intex/Bestway/in-ground pool
models, and a Lovelace dashboard card with a visual SVG of the pool.

## Features

- UI configuration (no YAML)
- Daily run duration computed from a temperature input (`T/2`, `T/3`
  below 13 °C), clamped, centered on a pivot hour with optional midday
  break
- **Water sensor mode** (probe directly) **or air-based thermal model**
  (first-order RC, persisted across restarts)
- **Pool model catalog**: Intex Easy Set / Metal Frame / Prism Frame /
  Ultra XTR / Rectangular Frame, Bestway Steel Pro / Steel Pro Max /
  Power Steel / Hydrium, plus generic in-ground sizes — drives the
  thermal model defaults and the dashboard visual
- Optional forecast sensor → forces max hours during heatwaves
- Optional electrolyzer switch with configurable post-start / pre-stop
  margins **and** min/max water-temperature cutoffs (cell off below
  15 °C / above 40 °C by default)
- Optional low-water binary sensor blocks the pump when triggered
- Native entities (sensors, binary sensors, mode selector) attached to a
  single device
- English and French translations included
- Lovelace dashboard card with an SVG of the pool (correct shape and
  proportions, color reflects pump state)

See the [README](https://github.com/Shad107/ha-pool_pump#readme) for full
details and migration notes from upstream.
