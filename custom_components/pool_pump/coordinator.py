"""DataUpdateCoordinator for Pool Pump Manager.

Schedule logic (no external lib):
  - total_hours = T/2 (or T/3 below 13°C), clamped to [min_hours, max_hours]
  - if a forecast max sensor reads at or above the heatwave threshold,
    total_hours is forced to max_hours
  - the run is centered on the configured pivot hour (default 14:00 local),
    optionally split into two with a midday break

Temperature source:
  - `water` mode: the configured sensor IS the water temperature (probe).
  - `air_model` mode: the configured sensor is air temperature; the
    coordinator integrates a 1st-order thermal model with configurable
    time constant tau to estimate water temperature. State is persisted
    across HA restarts via `homeassistant.helpers.storage.Store`.

Electrolyzer (optional):
  - On only inside [run.start + post_start_delay, run.end - pre_stop_delay]
  - Blocked when water temperature is below `electrolyzer_min_temp` or
    above `electrolyzer_max_temp` (literature-backed cell protection)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CHEM_PARAMS,
    COLD_THRESHOLD_CELSIUS,
    CONF_CHEMISTRY_ENABLED,
    CONF_CUSTOM_POOL_DEPTH,
    CONF_CUSTOM_POOL_INGROUND,
    CONF_CUSTOM_POOL_LENGTH,
    CONF_CUSTOM_POOL_SHAPE,
    CONF_CUSTOM_POOL_WIDTH,
    CONF_DURATION_AT_15C,
    CONF_DURATION_AT_20C,
    CONF_DURATION_AT_25C,
    CONF_DURATION_AT_30C,
    CONF_DURATION_AT_35C,
    CONF_DURATION_CURVE_ENABLED,
    CONF_EARLIEST_START_HOUR,
    CONF_FILTRATION_MULTIPLIER,
    CONF_LATEST_END_HOUR,
    CONF_SHOW_ILLUSTRATION,
    CONF_WINTERIZATION_OVERRIDE,
    DEFAULT_CHEMISTRY_ENABLED,
    DEFAULT_DURATION_AT_15C,
    DEFAULT_DURATION_AT_20C,
    DEFAULT_DURATION_AT_25C,
    DEFAULT_DURATION_AT_30C,
    DEFAULT_DURATION_AT_35C,
    DEFAULT_DURATION_CURVE_ENABLED,
    DEFAULT_EARLIEST_START_HOUR,
    DEFAULT_FILTRATION_MULTIPLIER,
    DEFAULT_LATEST_END_HOUR,
    DEFAULT_SHOW_ILLUSTRATION,
    DEFAULT_WINTERIZATION_OVERRIDE,
    ROUTINES,
    CONF_AUTOTUNE_ENABLED,
    CONF_AUTOTUNE_WINDOW_DAYS,
    CONF_BREAK_HOURS,
    CONF_ELECTROLYZER_MAX_TEMP,
    CONF_ELECTROLYZER_MIN_TEMP,
    CONF_ELECTROLYZER_POST_START_DELAY,
    CONF_ELECTROLYZER_PRE_STOP_DELAY,
    CONF_ELECTROLYZER_SWITCH,
    CONF_FORECAST_SENSOR,
    CONF_HEATWAVE_THRESHOLD,
    CONF_MAX_HOURS,
    CONF_MIN_HOURS,
    CONF_PIVOT_HOUR,
    CONF_BACKWASH_DURATION_MINUTES,
    CONF_ELECTROLYZER_POWER_SENSOR,
    CONF_POOL_HAS_COVER,
    CONF_POOL_IMAGE_URL,
    CONF_POOL_PRESET,
    CONF_PUMP_POWER_SENSOR,
    CONF_PUMP_SHORT_CYCLE_THRESHOLD,
    CONF_PUMP_SWITCH,
    CONF_WEATHER_ENTITY,
    CONF_WINTERIZATION_END_MONTH,
    CONF_WINTERIZATION_START_MONTH,
    CONF_SMOOTHING_WINDOW_HOURS,
    CONF_SOLAR_COEFFICIENT,
    CONF_SOLAR_INSTALLED_WATTS,
    CONF_SOLAR_PEAK_SENSOR,
    CONF_SOLAR_POWER_SENSOR,
    CONF_TAU_HOURS,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_OFFSET,
    CONF_TEMPERATURE_SENSOR,
    CONF_WATER_LEVEL_CRITICAL,
    DEFAULT_AUTOTUNE_ENABLED,
    DEFAULT_AUTOTUNE_HALF_LIFE_DAYS,
    DEFAULT_AUTOTUNE_MAX_OFFSET,
    DEFAULT_AUTOTUNE_WINDOW_DAYS,
    DEFAULT_BACKWASH_DURATION_MINUTES,
    DEFAULT_ELECTROLYZER_MAX_TEMP,
    DEFAULT_ELECTROLYZER_MIN_TEMP,
    DEFAULT_FORECAST_PREHEAT_THRESHOLD,
    DEFAULT_PUMP_SHORT_CYCLE_THRESHOLD,
    DEFAULT_SMOOTHING_WINDOW_HOURS,
    DEFAULT_SOLAR_COEFFICIENT,
    DEFAULT_TAU_HOURS,
    DEFAULT_TEMPERATURE_MODE,
    DEFAULT_TEMPERATURE_OFFSET,
    DOMAIN,
    ELEC_BLOCK_BACKWASH,
    ELEC_BLOCK_MANUAL,
    ELEC_BLOCK_MARGIN,
    ELEC_BLOCK_NONE,
    ELEC_BLOCK_PUMP_OFF,
    ELEC_BLOCK_PUMP_UNAVAILABLE,
    ELEC_BLOCK_TEMP_HIGH,
    ELEC_BLOCK_TEMP_LOW,
    ELEC_BLOCK_MAINTENANCE,
    ELEC_BLOCK_PUMP_ONLY,
    ELEC_BLOCK_WINTERIZATION,
    MODE_AUTO,
    MODE_MAINTENANCE,
    MODE_OFF,
    MODE_ON,
    MODE_PUMP_ONLY,
    RUN_REASON_AUTO,
    RUN_REASON_BACKWASH,
    RUN_REASON_HEATWAVE,
    RUN_REASON_MANUAL_OFF,
    RUN_REASON_MANUAL_ON,
    RUN_REASON_MAINTENANCE,
    RUN_REASON_OFF,
    RUN_REASON_PUMP_ONLY,
    RUN_REASON_WATER_LOW,
    RUN_REASON_WINTERIZATION,
    STORAGE_KEY_TEMPLATE,
    STORAGE_VERSION,
    SWITCH_REAPPLY_COOLDOWN,
    TEMP_MODE_AIR_MODEL,
    TEMP_MODE_WATER,
    UPDATE_INTERVAL,
)
from .presets import (
    PRESET_CUSTOM,
    build_custom_preset,
    compute_solar_coefficient,
    compute_tau_hours,
    get_preset,
    render_pool_svg,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class Run:
    """A single scheduled pump run."""

    start: datetime
    end: datetime

    def contains(self, when: datetime) -> bool:
        return self.start <= when < self.end


@dataclass
class ChemistryReading:
    """One chemistry parameter reading + diagnosis."""

    key: str
    label: str
    unit: str
    value: float | None
    target: float
    target_low: float
    target_high: float
    status: str  # "ok", "low", "high", "unknown"


@dataclass
class ChemistryRecommendation:
    """A suggested dose + pump action for a specific issue."""

    issue_key: str  # e.g. "ph_high", "free_chlorine_low"
    severity: str  # "info", "warning", "critical"
    title: str
    product: str
    dose_g: float | None = None
    dose_ml: float | None = None
    pump_action: str = "auto"  # "maintenance", "auto", "off"
    pump_duration_min: int = 0
    notes: str = ""


@dataclass
class PoolPumpData:
    """Snapshot of the coordinator state, consumed by entities."""

    temperature_used: float | None = None
    temperature_mode: str = TEMP_MODE_WATER
    air_temperature_raw: float | None = None
    forecast_value: float | None = None
    duration_hours: float = 0.0
    runs: list[Run] = field(default_factory=list)
    next_start: datetime | None = None
    next_end: datetime | None = None
    pump_should_be_on: bool = False
    electrolyzer_should_be_on: bool = False
    electrolyzer_block_reason: str = ELEC_BLOCK_NONE
    reason: str = RUN_REASON_OFF
    mode: str = MODE_AUTO
    heatwave_active: bool = False
    pool_preset: dict | None = None
    pool_svg: str = ""
    pool_image_url: str | None = None
    pool_bundled_url: str | None = None
    pump_available: bool = True
    electrolyzer_available: bool = True
    air_temperature_smoothed: float | None = None
    water_modeled_raw: float | None = None
    learned_temperature_offset: float = 0.0
    calibration_points: int = 0
    forecast_temperature_max_24h: float | None = None
    forecast_condition: str | None = None
    forecast_preheat_active: bool = False
    solar_power_w: float | None = None
    solar_peak_w: float | None = None
    solar_fraction: float = 0.0
    solar_coefficient_effective: float = 0.0
    tau_hours_effective: float = 0.0
    pump_power_w: float | None = None
    electrolyzer_power_w: float | None = None
    total_power_w: float | None = None
    energy_today_kwh: float = 0.0
    energy_total_kwh: float = 0.0
    cell_hours_total: float = 0.0
    backwash_active: bool = False
    backwash_ends_at: datetime | None = None
    winterization_active: bool = False
    maintenance_active: bool = False
    maintenance_ends_at: datetime | None = None
    chemistry: list[ChemistryReading] = field(default_factory=list)
    chemistry_recommendations: list[ChemistryRecommendation] = field(default_factory=list)
    mode_time_today: dict[str, float] = field(default_factory=dict)  # mode → seconds
    active_routine: dict | None = None  # {key, label, ends_at, dose_info}
    # v0.14 UI flags consumed by the Lovelace card to conditionally
    # render sections. None of these affect the integration's logic.
    has_electrolyzer: bool = True
    show_illustration: bool = True
    chemistry_enabled: bool = True


def compute_duration_from_curve(
    temperature: float, anchors: list[tuple[float, float]]
) -> float:
    """Linear interpolation between (temp, hours) anchor points.

    `anchors` is a list of (temperature_C, hours) tuples, sorted by
    temperature. Outside the bracket, the closest anchor is reused —
    we don't extrapolate, because the user already vetted the bounds
    they're interested in.

    Returns hours (unclamped — the caller clamps to [min_h, max_h]).
    """
    if not anchors:
        return 0.0
    if temperature <= anchors[0][0]:
        return anchors[0][1]
    if temperature >= anchors[-1][0]:
        return anchors[-1][1]
    for i in range(len(anchors) - 1):
        t0, h0 = anchors[i]
        t1, h1 = anchors[i + 1]
        if t0 <= temperature <= t1:
            ratio = (temperature - t0) / (t1 - t0) if t1 != t0 else 0.0
            return h0 + ratio * (h1 - h0)
    return anchors[-1][1]  # unreachable, here for safety


def compute_duration(
    temperature: float,
    *,
    min_hours: float,
    max_hours: float,
    forecast_value: float | None,
    heatwave_threshold: float,
    curve_anchors: list[tuple[float, float]] | None = None,
) -> tuple[float, bool]:
    """Return (duration_hours, heatwave_active) for the given inputs.

    When `curve_anchors` is provided (and non-empty), the duration is
    interpolated from the user curve instead of the built-in
    T/2 (T/3 below 13°C) formula. Heatwave override still wins —
    canicule forces max_hours regardless of the curve, by design
    (users typically want max filtration on a heat-spike day even if
    their curve says less).
    """
    heatwave_active = (
        forecast_value is not None and forecast_value >= heatwave_threshold
    )
    if heatwave_active:
        return max_hours, True

    if curve_anchors:
        base = compute_duration_from_curve(temperature, curve_anchors)
    elif temperature < COLD_THRESHOLD_CELSIUS:
        base = temperature / 3.0
    else:
        base = temperature / 2.0

    return max(min_hours, min(max_hours, base)), False


def build_runs(
    pivot: datetime, duration_hours: float, break_hours: float
) -> list[Run]:
    """Build run intervals centered on pivot, optionally split by a break."""
    total = timedelta(hours=duration_hours)
    if break_hours <= 0 or duration_hours <= break_hours:
        return [Run(start=pivot - total / 2, end=pivot + total / 2)]

    effective = total - timedelta(hours=break_hours)
    half_break = timedelta(hours=break_hours) / 2
    first_len = effective / 3
    second_len = effective - first_len
    first_start = pivot - half_break - first_len
    first_end = pivot - half_break
    second_start = pivot + half_break
    second_end = pivot + half_break + second_len
    return [Run(first_start, first_end), Run(second_start, second_end)]


def update_thermal_model(
    current_water: float | None,
    air_temp: float,
    *,
    offset: float,
    tau_hours: float,
    dt_seconds: float,
    solar_fraction: float = 0.0,
    solar_coefficient: float = 0.0,
) -> float:
    """First-order RC model with optional solar gain term.

        dT_w/dt = (T_air + offset - T_w) / tau   +   k_sun * solar_fraction

    Discretized over dt_seconds:
        T_w[n+1] = T_w[n] + alpha * (T_target - T_w[n]) + k * solar_fraction * dt/3600
    with alpha = 1 - exp(-dt/tau) for numerical stability across long gaps.

    `solar_fraction` ∈ [0, 1] is current solar input normalized to peak
    (typically `P_solar / P_peak`). `solar_coefficient` is the °C/hour
    heating rate at full sun (k_sun); when zero, the solar term is
    disabled.

    If no prior state is known, the model bootstraps at T_air + offset.
    """
    from math import exp

    target = air_temp + offset
    if current_water is None or tau_hours <= 0 or dt_seconds < 0:
        return target

    tau_seconds = tau_hours * 3600.0
    alpha = 1.0 - exp(-dt_seconds / tau_seconds)
    new = current_water + alpha * (target - current_water)

    if solar_coefficient > 0 and solar_fraction > 0:
        new += solar_coefficient * solar_fraction * (dt_seconds / 3600.0)

    return new


def rolling_mean(samples: list[tuple[datetime, float]], window: timedelta) -> float | None:
    """Mean of samples within `window` before the latest sample.

    `samples` is a list of (timestamp, value) tuples, sorted oldest-first.
    Returns None if no sample is in-window.
    """
    if not samples:
        return None
    cutoff = samples[-1][0] - window
    kept = [v for (t, v) in samples if t >= cutoff]
    return sum(kept) / len(kept) if kept else None


def _read_float(hass: HomeAssistant, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, None, ""):
        return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


def _pivot_for_day(day: datetime, pivot_hour: int) -> datetime:
    return dt_util.as_local(day).replace(
        hour=pivot_hour, minute=0, second=0, microsecond=0
    )


def _electrolyzer_window_ok(
    runs: list[Run], now: datetime, post_start: int, pre_stop: int
) -> bool:
    """True iff `now` falls inside a run with the post-start and pre-stop margins applied."""
    post_start_td = timedelta(seconds=post_start)
    pre_stop_td = timedelta(seconds=pre_stop)
    for r in runs:
        if r.start + post_start_td <= now < r.end - pre_stop_td:
            return True
    return False


class PoolPumpCoordinator(DataUpdateCoordinator[PoolPumpData]):
    """Compute schedule and drive the pump and electrolyzer switches."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, options: dict[str, Any]
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.entry_id = entry_id
        self.options = options
        self.mode: str = MODE_AUTO
        self._water_modeled: float | None = None
        self._last_model_update: datetime | None = None
        self._store: Store = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY_TEMPLATE.format(entry_id=entry_id),
        )
        # Tracks the last availability seen, so we can log on transition only.
        self._availability_state: dict[str, bool] = {}
        # Rolling buffer of (timestamp, air_temp) samples for the smoothing
        # window. Capped at ~3000 entries (≈50h of minutely ticks).
        self._air_samples: list[tuple[datetime, float]] = []
        self._max_samples: int = 3000
        # Energy accumulators (Riemann sum of power × dt every tick).
        self._energy_today_kwh: float = 0.0
        self._energy_total_kwh: float = 0.0
        self._last_energy_update: datetime | None = None
        self._energy_today_date: str | None = None  # YYYY-MM-DD for daily reset
        # Cell lifetime accounting and pump short-cycle debounce
        self._cell_hours_total: float = 0.0
        self._last_cell_update: datetime | None = None
        self._pump_continuous_on_since: datetime | None = None
        self._pump_last_off: datetime | None = None
        # Backwash mode: when active, pump ON + cell OFF until ends_at.
        self._backwash_ends_at: datetime | None = None
        # Generic mode timer: when this fires, mode reverts to AUTO.
        # Used by maintenance_start, backwash (separately tracked), and
        # the start_routine service for the preset chemistry routines.
        self._mode_timer_ends_at: datetime | None = None
        self._mode_timer_key: str | None = None  # routine key (display only)
        self._mode_timer_dose_info: dict | None = None  # {product, dose_g, dose_ml, notes}
        # Number entities (per chemistry key) registered by the number platform.
        self._chemistry_numbers: dict[str, "NumberEntity"] = {}
        # Per-mode cumulative time today (seconds). Resets at midnight.
        self._mode_time_today: dict[str, float] = {}
        self._mode_time_date: str | None = None  # YYYY-MM-DD
        self._last_mode_tick: datetime | None = None
        # One-shot timer used to refresh exactly when the post_start
        # margin expires, instead of waiting for the next 60-second tick.
        self._deferred_refresh_unsub = None
        # Auto-tuning calibration: list of (timestamp, delta) where
        # delta = real_value - modeled_value at calibration time. The
        # weighted mean of recent deltas becomes the learned_offset.
        self._calibrations: list[tuple[datetime, float]] = []
        self._learned_offset: float = 0.0
        # Forecast cache (refreshed at most once per hour to avoid
        # spamming the weather entity).
        self._forecast_cache: dict[str, Any] = {}
        self._forecast_cache_at: datetime | None = None
        # Last switch action per entity: {entity_id: (sent_at, target_on)}.
        # Enforces SWITCH_REAPPLY_COOLDOWN so a Tuya plug that keeps flipping
        # back to the wrong state doesn't trigger a turn_off every tick.
        self._switch_last_action: dict[str, tuple[datetime, bool]] = {}
        # v0.16.5 debug: track the last _apply_switch call per entity so we
        # can correlate observed state changes with our own commands.
        # (sent_at_utc, service, reason)
        self._debug_last_call: dict[str, tuple[datetime, str, str]] = {}
        self._debug_unsubs: list = []
        pump_id = options.get(CONF_PUMP_SWITCH)
        elec_id = options.get(CONF_ELECTROLYZER_SWITCH)
        watched = [e for e in (pump_id, elec_id) if e]
        if watched:
            self._debug_unsubs.append(
                async_track_state_change_event(
                    hass, watched, self._debug_on_switch_change
                )
            )

    async def async_load_persisted(self) -> None:
        """Load the modeled water temp + air samples from disk (once at init)."""
        stored = await self._store.async_load()
        if not stored:
            return
        self._water_modeled = stored.get("water_temp")
        # Calibration history & learned offset
        for entry in stored.get("calibrations", []) or []:
            try:
                ts = datetime.fromisoformat(entry["t"])
                self._calibrations.append((ts, float(entry["d"])))
            except (KeyError, ValueError, TypeError):
                continue
        try:
            self._learned_offset = float(stored.get("learned_offset") or 0.0)
        except (TypeError, ValueError):
            self._learned_offset = 0.0
        last = stored.get("last_update")
        if last:
            try:
                self._last_model_update = datetime.fromisoformat(last)
            except ValueError:
                self._last_model_update = None
        # Restore air sample history so the rolling mean is warm after restart
        for entry in stored.get("air_samples", []) or []:
            try:
                ts = datetime.fromisoformat(entry["t"])
                self._air_samples.append((ts, float(entry["v"])))
            except (KeyError, ValueError, TypeError):
                continue
        # Energy accumulators
        self._energy_today_kwh = float(stored.get("energy_today_kwh") or 0.0)
        self._energy_total_kwh = float(stored.get("energy_total_kwh") or 0.0)
        self._energy_today_date = stored.get("energy_today_date")
        last_energy = stored.get("last_energy_update")
        if last_energy:
            try:
                self._last_energy_update = datetime.fromisoformat(last_energy)
            except ValueError:
                self._last_energy_update = None
        # Mode-time today
        self._mode_time_today = dict(stored.get("mode_time_today") or {})
        self._mode_time_date = stored.get("mode_time_date")
        last_mt = stored.get("last_mode_tick")
        if last_mt:
            try:
                self._last_mode_tick = datetime.fromisoformat(last_mt)
            except ValueError:
                self._last_mode_tick = None
        # Cell-hour accumulator
        self._cell_hours_total = float(stored.get("cell_hours_total") or 0.0)
        last_cell = stored.get("last_cell_update")
        if last_cell:
            try:
                self._last_cell_update = datetime.fromisoformat(last_cell)
            except ValueError:
                self._last_cell_update = None
        # Backwash timer
        bw = stored.get("backwash_ends_at")
        if bw:
            try:
                self._backwash_ends_at = datetime.fromisoformat(bw)
            except ValueError:
                self._backwash_ends_at = None
        # Mode timer (generic routine auto-revert). Keep
        # `maintenance_ends_at` for backward compat with v0.11.x stores.
        mt = stored.get("mode_timer_ends_at") or stored.get("maintenance_ends_at")
        if mt:
            try:
                self._mode_timer_ends_at = datetime.fromisoformat(mt)
            except ValueError:
                self._mode_timer_ends_at = None
        self._mode_timer_key = stored.get("mode_timer_key")
        self._mode_timer_dose_info = stored.get("mode_timer_dose_info")
        # Pump continuous-on tracker: persist across restarts so the
        # cell margin doesn't reset every reboot. Without this, HA
        # restart → tracker None → first tick falls back to
        # pump.last_changed (which HA itself resets at restart) → the
        # cell gets force-cycled OFF for ~post_start_delay seconds.
        pcos = stored.get("pump_continuous_on_since")
        if pcos:
            try:
                self._pump_continuous_on_since = datetime.fromisoformat(pcos)
            except ValueError:
                self._pump_continuous_on_since = None
        plo = stored.get("pump_last_off")
        if plo:
            try:
                self._pump_last_off = datetime.fromisoformat(plo)
            except ValueError:
                self._pump_last_off = None

    async def _async_save_model(self) -> None:
        await self._store.async_save(
            {
                "water_temp": self._water_modeled,
                "last_update": (
                    self._last_model_update.isoformat()
                    if self._last_model_update
                    else None
                ),
                "air_samples": [
                    {"t": t.isoformat(), "v": v}
                    for (t, v) in self._air_samples[-self._max_samples:]
                ],
                "energy_today_kwh": self._energy_today_kwh,
                "energy_total_kwh": self._energy_total_kwh,
                "energy_today_date": self._energy_today_date,
                "last_energy_update": (
                    self._last_energy_update.isoformat()
                    if self._last_energy_update
                    else None
                ),
                "cell_hours_total": self._cell_hours_total,
                "last_cell_update": (
                    self._last_cell_update.isoformat()
                    if self._last_cell_update
                    else None
                ),
                "backwash_ends_at": (
                    self._backwash_ends_at.isoformat()
                    if self._backwash_ends_at
                    else None
                ),
                "mode_timer_ends_at": (
                    self._mode_timer_ends_at.isoformat()
                    if self._mode_timer_ends_at
                    else None
                ),
                "mode_timer_key": self._mode_timer_key,
                "mode_timer_dose_info": self._mode_timer_dose_info,
                "pump_continuous_on_since": (
                    self._pump_continuous_on_since.isoformat()
                    if self._pump_continuous_on_since
                    else None
                ),
                "pump_last_off": (
                    self._pump_last_off.isoformat()
                    if self._pump_last_off
                    else None
                ),
                "calibrations": [
                    {"t": t.isoformat(), "d": d}
                    for (t, d) in self._calibrations[-200:]
                ],
                "learned_offset": self._learned_offset,
                "mode_time_today": self._mode_time_today,
                "mode_time_date": self._mode_time_date,
                "last_mode_tick": (
                    self._last_mode_tick.isoformat()
                    if self._last_mode_tick
                    else None
                ),
            }
        )

    def _schedule_deferred_refresh(self, seconds: float) -> None:
        """Schedule a one-shot refresh in `seconds`, replacing any pending one.

        Used to wake up exactly when the post_start margin expires, so the
        electrolyzer turns ON immediately instead of waiting up to 60 s for
        the next coordinator tick.
        """
        if self._deferred_refresh_unsub is not None:
            self._deferred_refresh_unsub()
            self._deferred_refresh_unsub = None

        async def _fire(_now):
            self._deferred_refresh_unsub = None
            await self.async_request_refresh()

        self._deferred_refresh_unsub = async_call_later(
            self.hass, max(1.0, seconds), _fire
        )

    def set_mode(self, mode: str) -> None:
        """Change manual mode and force a refresh."""
        self.mode = mode
        self.hass.async_create_task(self.async_request_refresh())

    def reset_water_model(self, value: float | None = None) -> None:
        """Reset the modeled water temperature, recording a calibration point.

        If `value` is None, drop the persisted state so the model
        re-bootstraps from the next air sample (no calibration recorded).

        If a value is given, treat it as the ground-truth water
        temperature: record the delta (value - modeled_before) as a new
        calibration sample, recompute the learned offset, then reset
        the model so that displayed temperature equals `value`.
        """
        if value is not None and self._water_modeled is not None:
            delta = value - self._water_modeled
            now = dt_util.now()
            self._calibrations.append((now, delta))
            # Cap to last 365 days to bound storage
            cutoff = now - timedelta(days=365)
            self._calibrations = [(t, d) for (t, d) in self._calibrations if t >= cutoff]
            self._recompute_learned_offset()
            # Reset model state so T_used = modeled + learned_offset == value
            self._water_modeled = value - self._learned_offset
        elif value is not None:
            self._water_modeled = value - self._learned_offset
        else:
            self._water_modeled = None

        self._last_model_update = None
        self._air_samples = []
        self.hass.async_create_task(self._async_save_model())
        self.hass.async_create_task(self.async_request_refresh())

    def clear_calibration(self) -> None:
        """Forget all calibration points and the learned offset."""
        self._calibrations = []
        self._learned_offset = 0.0
        self.hass.async_create_task(self._async_save_model())
        self.hass.async_create_task(self.async_request_refresh())

    def _build_chemistry_diagnosis(
        self, volume_m3: float | None
    ) -> tuple[list[ChemistryReading], list[ChemistryRecommendation]]:
        """Read all chemistry params + generate dose recommendations.

        Volume-aware dosing per piscinist-standard formulas:
            pH−  : HCl 33%, ~10 mL/m³ per 0.1 pH to drop
            pH+  : Na₂CO₃, ~12 g/m³ per 0.1 pH to raise
            Cl   : HTH 65%, ~1.5 g/m³ per ppm to raise
            TAC  : bicarbonate de sodium, ~17 g/m³ per 10 ppm
            TH   : CaCl₂, ~11 g/m³ per 10 ppm (no down-dose, only dilution)
            CYA  : stabilisant cyanurique, ~13 g/m³ per 10 ppm
            Sel  : (target − current) × volume / 1000 kg

        Volume falls back to 30 m³ if no preset configured (warns user
        in the recommendation `notes`).
        """
        readings: list[ChemistryReading] = []
        recos: list[ChemistryRecommendation] = []
        vol = float(volume_m3) if volume_m3 else 30.0
        vol_warning = "" if volume_m3 else "Volume estimé à 30 m³ (configure un preset)"

        # Read all values + build the diagnosis records.
        values: dict[str, float | None] = {}
        for key, label, unit, _vmin, _vmax, _step, tgt, low, high, _on in CHEM_PARAMS:
            v = self._read_chemistry_value(key)
            values[key] = v
            if v is None:
                status = "unknown"
            elif v < low:
                status = "low"
            elif v > high:
                status = "high"
            else:
                status = "ok"
            readings.append(
                ChemistryReading(
                    key=key, label=label, unit=unit, value=v,
                    target=tgt, target_low=low, target_high=high, status=status,
                )
            )

        # === Generate volume-aware recommendations ===
        # pH first (do NEVER mix pH and chlorine on the same maintenance window).
        ph = values.get("ph")
        if ph is not None and ph > 7.6:
            delta = round((ph - 7.4) / 0.1, 1)
            dose_ml = round(10 * vol * delta, 0)
            recos.append(ChemistryRecommendation(
                issue_key="ph_high", severity="warning",
                title=f"pH élevé ({ph:.1f}) → cible 7.4",
                product="pH− (HCl 33%)",
                dose_ml=dose_ml,
                pump_action="maintenance", pump_duration_min=180,
                notes=(vol_warning or "Verser près du refoulement, jamais en surface."),
            ))
        elif ph is not None and ph < 7.2:
            delta = round((7.4 - ph) / 0.1, 1)
            dose_g = round(12 * vol * delta, 0)
            recos.append(ChemistryRecommendation(
                issue_key="ph_low", severity="warning",
                title=f"pH bas ({ph:.1f}) → cible 7.4",
                product="pH+ (carbonate de sodium Na₂CO₃)",
                dose_g=dose_g,
                pump_action="maintenance", pump_duration_min=180,
                notes=(vol_warning or "Dissoudre dans seau d'eau, verser progressivement."),
            ))

        # Free chlorine — pay attention to chloramines for breakpoint.
        fc = values.get("free_chlorine")
        tc = values.get("total_chlorine")
        chloramines = (
            tc - fc if (tc is not None and fc is not None and tc >= fc) else None
        )
        if fc is not None and fc < 1.0:
            if chloramines is not None and chloramines >= 0.3:
                # Breakpoint shock: need ~10× chloramines to break combined Cl.
                target_ppm = max(5.0, chloramines * 10)
                dose_g = round(1.5 * vol * target_ppm, 0)
                recos.append(ChemistryRecommendation(
                    issue_key="free_chlorine_breakpoint", severity="critical",
                    title=f"Chlore libre {fc:.1f} ppm + chloramines {chloramines:.1f} ppm → breakpoint shock",
                    product="Chlore choc (HTH 65% ou dichloroisocyanurate)",
                    dose_g=dose_g,
                    pump_action="maintenance", pump_duration_min=360,
                    notes="Dose forte pour casser le chlore combiné. NE PAS mélanger avec pH dans la même heure.",
                ))
            else:
                target_ppm = 2.0
                dose_g = round(1.5 * vol * (target_ppm - fc), 0)
                recos.append(ChemistryRecommendation(
                    issue_key="free_chlorine_low", severity="warning",
                    title=f"Chlore libre bas ({fc:.1f} ppm) → cible 2 ppm",
                    product="Chlore choc (HTH 65%)",
                    dose_g=dose_g,
                    pump_action="maintenance", pump_duration_min=240,
                    notes="Ou laisser la cellule remonter en mode Auto si la production suit.",
                ))
        elif fc is not None and fc > 5.0:
            recos.append(ChemistryRecommendation(
                issue_key="free_chlorine_high", severity="info",
                title=f"Chlore libre élevé ({fc:.1f} ppm)",
                product="Attendre",
                pump_action="auto", pump_duration_min=0,
                notes="Baisser la production cellule ou attendre 24-48h de dégradation UV.",
            ))

        # TAC
        tac = values.get("tac")
        if tac is not None and tac < 80:
            delta_ppm = 100 - tac
            dose_g = round(17 * vol * (delta_ppm / 10), 0)
            recos.append(ChemistryRecommendation(
                issue_key="tac_low", severity="warning",
                title=f"TAC bas ({tac:.0f} ppm) → cible 100",
                product="Bicarbonate de sodium",
                dose_g=dose_g,
                pump_action="maintenance", pump_duration_min=180,
                notes="Aide à stabiliser le pH. Ajouter en 2 doses si delta > 30 ppm.",
            ))
        elif tac is not None and tac > 150:
            recos.append(ChemistryRecommendation(
                issue_key="tac_high", severity="info",
                title=f"TAC élevé ({tac:.0f} ppm)",
                product="Renouvellement partiel d'eau",
                pump_action="auto", pump_duration_min=0,
                notes="Pas de chimie pour baisser le TAC, juste diluer.",
            ))

        # CYA
        cya = values.get("cya")
        if cya is not None and cya < 30:
            delta_ppm = 40 - cya
            dose_g = round(13 * vol * (delta_ppm / 10), 0)
            recos.append(ChemistryRecommendation(
                issue_key="cya_low", severity="info",
                title=f"CYA bas ({cya:.0f} ppm) → cible 40",
                product="Stabilisant (acide cyanurique)",
                dose_g=dose_g,
                pump_action="maintenance", pump_duration_min=1440,
                notes="Se dissout lentement, pompe 24h. Verser dans skimmer.",
            ))
        elif cya is not None and cya > 80:
            recos.append(ChemistryRecommendation(
                issue_key="cya_high", severity="warning",
                title=f"CYA trop élevé ({cya:.0f} ppm) — bloque le chlore",
                product="Renouvellement partiel d'eau",
                pump_action="auto", pump_duration_min=0,
                notes="Renouveler ~30% du volume si CYA > 100 ppm.",
            ))

        # TH
        th = values.get("th")
        if th is not None and th < 100:
            delta_ppm = 200 - th
            dose_g = round(11 * vol * (delta_ppm / 10), 0)
            recos.append(ChemistryRecommendation(
                issue_key="th_low", severity="info",
                title=f"TH bas ({th:.0f} ppm) → cible 200",
                product="Chlorure de calcium (CaCl₂)",
                dose_g=dose_g,
                pump_action="maintenance", pump_duration_min=180,
                notes="Eau trop douce = liner et inox attaqués.",
            ))
        elif th is not None and th > 500:
            recos.append(ChemistryRecommendation(
                issue_key="th_high", severity="warning",
                title=f"TH élevé ({th:.0f} ppm) — risque calcaire",
                product="Séquestrant calcaire",
                pump_action="maintenance", pump_duration_min=180,
                notes="Ou renouvellement partiel d'eau (~30%).",
            ))

        # Salt (saltwater chlorinator pools)
        salt = values.get("salt")
        if salt is not None and salt < 3000:
            kg = round((4000 - salt) * vol / 1000, 1)
            recos.append(ChemistryRecommendation(
                issue_key="salt_low", severity="warning",
                title=f"Sel bas ({salt:.0f} ppm) — cellule sous-alimentée",
                product="Sel piscine spécial électrolyse",
                dose_g=kg * 1000,
                pump_action="maintenance", pump_duration_min=240,
                notes="Verser dans skimmer en plusieurs fois, dissolution complète en 24h.",
            ))

        return readings, recos

    def _recompute_learned_offset(self) -> None:
        """Recompute the EMA-weighted offset from recent calibrations.

        Each calibration is weighted by 2^(-age_days / half_life), so
        recent ones dominate but older corrections still contribute.
        The result is clamped to ±DEFAULT_AUTOTUNE_MAX_OFFSET so a
        single bad calibration can't blow up the model.
        """
        if not self._calibrations:
            self._learned_offset = 0.0
            return

        window_days = float(
            self.options.get(
                CONF_AUTOTUNE_WINDOW_DAYS, DEFAULT_AUTOTUNE_WINDOW_DAYS
            )
        )
        half_life = DEFAULT_AUTOTUNE_HALF_LIFE_DAYS
        now = dt_util.now()
        cutoff = now - timedelta(days=window_days)
        recent = [(t, d) for (t, d) in self._calibrations if t >= cutoff]
        if not recent:
            self._learned_offset = 0.0
            return

        total_w = 0.0
        total_wd = 0.0
        for (t, d) in recent:
            age_days = max(0.0, (now - t).total_seconds() / 86400.0)
            w = 2.0 ** (-age_days / half_life)
            total_w += w
            total_wd += w * d

        offset = total_wd / total_w if total_w > 0 else 0.0
        offset = max(
            -DEFAULT_AUTOTUNE_MAX_OFFSET,
            min(DEFAULT_AUTOTUNE_MAX_OFFSET, offset),
        )
        self._learned_offset = offset

    def trigger_backwash(self, duration_minutes: float | None = None) -> None:
        """Start a backwash cycle: pump ON + cell OFF for `duration_minutes`."""
        dur = float(
            duration_minutes
            if duration_minutes is not None
            else self.options.get(
                CONF_BACKWASH_DURATION_MINUTES, DEFAULT_BACKWASH_DURATION_MINUTES
            )
        )
        self._backwash_ends_at = dt_util.now() + timedelta(minutes=dur)
        _LOGGER.info("Backwash started: %.1f min (ends at %s)", dur, self._backwash_ends_at)
        self.hass.async_create_task(self.async_request_refresh())

    def cancel_backwash(self) -> None:
        """Cancel an in-progress backwash."""
        self._backwash_ends_at = None
        self.hass.async_create_task(self.async_request_refresh())

    def trigger_maintenance(self, duration_minutes: float) -> None:
        """Force pump ON + cell OFF for `duration_minutes`, then auto-revert.

        Convenience wrapper around the generic routine timer for the
        explicit "I just dosed something, mix it" workflow.
        """
        self._start_timed_mode(
            mode=MODE_MAINTENANCE,
            duration_minutes=float(duration_minutes),
            key="manual_maintenance",
        )

    def cancel_maintenance(self) -> None:
        """Cancel an in-progress maintenance cycle (and any active routine)."""
        self._mode_timer_ends_at = None
        self._mode_timer_key = None
        self._mode_timer_dose_info = None
        if self.mode == MODE_MAINTENANCE:
            self.mode = MODE_AUTO
        self.hass.async_create_task(self.async_request_refresh())

    def start_routine(self, routine_key: str) -> dict | None:
        """Start a preset routine (smart or manual).

        Smart routines (shock_chlorine, ph_adjust, tac_adjust,
        stabilizer_dissolve) pull the dose + duration from the live
        chemistry diagnosis. Manual ones (boost_cell, mix) use the
        hardcoded default duration.

        Returns the dose_info dict (for confirmation display) or None
        if the routine isn't applicable (e.g., shock_chlorine when
        free chlorine is already OK).
        """
        meta = next((r for r in ROUTINES if r[0] == routine_key), None)
        if meta is None:
            _LOGGER.warning("Unknown routine: %s", routine_key)
            return None
        _, label, _icon, target_mode, default_min, smart_prefix, _fav = meta

        dose_info: dict | None = None
        duration_min = default_min

        # For smart routines, look up the matching recommendation in the
        # most recently computed diagnosis (data may be None on cold start).
        if smart_prefix and self.data is not None:
            for reco in self.data.chemistry_recommendations:
                if reco.issue_key.startswith(smart_prefix):
                    dose_info = {
                        "product": reco.product,
                        "dose_g": reco.dose_g,
                        "dose_ml": reco.dose_ml,
                        "notes": reco.notes,
                        "title": reco.title,
                    }
                    if reco.pump_duration_min > 0:
                        duration_min = reco.pump_duration_min
                    break
            if dose_info is None:
                _LOGGER.info(
                    "Routine %s requested but no matching reco — applying default",
                    routine_key,
                )

        self._start_timed_mode(
            mode=target_mode,
            duration_minutes=duration_min,
            key=routine_key,
            dose_info=dose_info,
        )
        return dose_info

    def _start_timed_mode(
        self,
        mode: str,
        duration_minutes: float,
        key: str,
        dose_info: dict | None = None,
    ) -> None:
        """Set mode + arm the auto-revert-to-AUTO timer."""
        self.mode = mode
        self._mode_timer_ends_at = dt_util.now() + timedelta(minutes=duration_minutes)
        self._mode_timer_key = key
        self._mode_timer_dose_info = dose_info
        _LOGGER.info(
            "Routine %s started: mode=%s, %.0f min (ends %s)",
            key,
            mode,
            duration_minutes,
            self._mode_timer_ends_at,
        )
        self.hass.async_create_task(self.async_request_refresh())

    def register_chemistry_number(self, key: str, entity) -> None:
        """Track a number entity so the coordinator can read its value."""
        self._chemistry_numbers[key] = entity

    def reset_mode_time(self) -> None:
        """Wipe the per-mode time accumulators for today.

        Useful right after upgrading from a version with the v0.12.2 /
        v0.12.3 accounting bugs, when the counter carries forward a
        bogus history. Resets to zero, the next pump-on tick starts
        the fresh accumulation.
        """
        self._mode_time_today = {}
        self._mode_time_date = dt_util.now().date().isoformat()
        _LOGGER.info("mode_time_today reset")
        self.hass.async_create_task(self._async_save_model())
        self.hass.async_create_task(self.async_request_refresh())

    def _read_chemistry_value(self, key: str) -> float | None:
        """Resolve a chemistry reading: sensor override > number entity."""
        sensor_id = self.options.get(f"chem_{key}_sensor")
        if sensor_id:
            v = _read_float(self.hass, sensor_id)
            if v is not None:
                return v
        ent = self._chemistry_numbers.get(key)
        if ent is not None and getattr(ent, "_value", None) is not None:
            return float(ent._value)
        return None

    def set_chemistry_value(self, key: str, value: float) -> None:
        """Update a chemistry number entity from a service call."""
        ent = self._chemistry_numbers.get(key)
        if ent is None:
            _LOGGER.warning("Unknown chemistry key: %s", key)
            return
        ent._value = value
        try:
            ent.async_write_ha_state()
        except Exception:  # noqa: BLE001 — entity may not be added yet
            pass
        self.hass.async_create_task(self.async_request_refresh())

    @staticmethod
    def _is_winter_month(now: datetime, start: int, end: int) -> bool:
        """True if `now`'s month is within the winterization range.

        Handles year-wrap (e.g., start=11, end=3 means Nov, Dec, Jan, Feb, Mar).
        Setting both to 0 (or equal) means winterization disabled.
        """
        if not (1 <= start <= 12 and 1 <= end <= 12):
            return False
        if start == end:
            return False
        m = now.month
        if start <= end:
            return start <= m <= end
        # wraps year boundary
        return m >= start or m <= end

    async def _read_weather_forecast(self, now: datetime) -> None:
        """Refresh the cached 24-hour forecast from the configured weather entity.

        Cached for one hour to avoid hammering the weather service every tick.
        On any error (entity missing, service unsupported, malformed reply),
        silently skip — forecast is best-effort, not safety-critical.
        """
        weather_id = self.options.get(CONF_WEATHER_ENTITY)
        if not weather_id:
            self._forecast_cache = {}
            return
        if (
            self._forecast_cache_at is not None
            and (now - self._forecast_cache_at).total_seconds() < 3600
            and self._forecast_cache
        ):
            return
        try:
            resp = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": weather_id, "type": "hourly"},
                blocking=True,
                return_response=True,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            _LOGGER.debug("Weather forecast unavailable (%s): %s", weather_id, exc)
            return

        forecasts = (resp or {}).get(weather_id, {}).get("forecast") or []
        if not forecasts:
            return

        end = now + timedelta(hours=24)
        temps: list[float] = []
        conditions: list[str] = []
        for f in forecasts:
            raw_dt = f.get("datetime", "")
            try:
                ts = datetime.fromisoformat(str(raw_dt).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            if ts > end:
                break
            t = f.get("temperature")
            if t is not None:
                try:
                    temps.append(float(t))
                except (TypeError, ValueError):
                    pass
            c = f.get("condition")
            if c:
                conditions.append(str(c))

        from collections import Counter

        self._forecast_cache = {
            "max_temp": max(temps) if temps else None,
            "min_temp": min(temps) if temps else None,
            "condition": (
                Counter(conditions).most_common(1)[0][0] if conditions else None
            ),
        }
        self._forecast_cache_at = now

    async def _async_update_data(self) -> PoolPumpData:
        now = dt_util.now()
        data = PoolPumpData(mode=self.mode)

        # Per-mode "time the pump is actually doing work" accounting.
        # Resets daily. The dt is only attributed once we know whether
        # the pump is running this tick — see the block after the pump
        # decision below. We just handle the date rollover here.
        today_key = now.date().isoformat()
        if self._mode_time_date != today_key:
            self._mode_time_today = {}
            self._mode_time_date = today_key

        await self._read_weather_forecast(now)
        data.forecast_temperature_max_24h = self._forecast_cache.get("max_temp")
        data.forecast_condition = self._forecast_cache.get("condition")
        if data.forecast_temperature_max_24h is not None:
            data.forecast_preheat_active = (
                data.forecast_temperature_max_24h
                < DEFAULT_FORECAST_PREHEAT_THRESHOLD
            )

        temp_id: str = self.options[CONF_TEMPERATURE_SENSOR]
        forecast_id: str | None = self.options.get(CONF_FORECAST_SENSOR)
        water_low_id: str | None = self.options.get(CONF_WATER_LEVEL_CRITICAL)
        temp_mode: str = self.options.get(CONF_TEMPERATURE_MODE, DEFAULT_TEMPERATURE_MODE)
        data.temperature_mode = temp_mode

        min_h = float(self.options.get(CONF_MIN_HOURS, 2.0))
        max_h = float(self.options.get(CONF_MAX_HOURS, 24.0))
        break_h = float(self.options.get(CONF_BREAK_HOURS, 0.0))
        pivot_hour = int(self.options.get(CONF_PIVOT_HOUR, 14))
        heatwave_threshold = float(self.options.get(CONF_HEATWAVE_THRESHOLD, 28.0))
        post_start = int(self.options.get(CONF_ELECTROLYZER_POST_START_DELAY, 120))
        pre_stop = int(self.options.get(CONF_ELECTROLYZER_PRE_STOP_DELAY, 60))
        elec_min = float(
            self.options.get(CONF_ELECTROLYZER_MIN_TEMP, DEFAULT_ELECTROLYZER_MIN_TEMP)
        )
        elec_max = float(
            self.options.get(CONF_ELECTROLYZER_MAX_TEMP, DEFAULT_ELECTROLYZER_MAX_TEMP)
        )
        offset = float(
            self.options.get(CONF_TEMPERATURE_OFFSET, DEFAULT_TEMPERATURE_OFFSET)
        )

        preset_slug = self.options.get(CONF_POOL_PRESET)
        if preset_slug == PRESET_CUSTOM:
            # Build a synthetic preset from the user-provided dimensions.
            # Falls back to None (no preset) if the user picked custom
            # without filling in the fields — coordinator then uses
            # default τ from CONF_TAU_HOURS.
            preset = build_custom_preset(
                length_cm=self.options.get(CONF_CUSTOM_POOL_LENGTH),
                width_cm=self.options.get(CONF_CUSTOM_POOL_WIDTH),
                depth_cm=self.options.get(CONF_CUSTOM_POOL_DEPTH),
                shape=self.options.get(CONF_CUSTOM_POOL_SHAPE, "rect"),
                inground=bool(self.options.get(CONF_CUSTOM_POOL_INGROUND)),
            )
        else:
            preset = get_preset(preset_slug) if preset_slug else None
        data.pool_preset = preset

        # Tau: explicit option wins; otherwise derive from the preset if any.
        if self.options.get(CONF_TAU_HOURS) is not None:
            tau_hours = float(self.options[CONF_TAU_HOURS])
        elif preset is not None:
            tau_hours = compute_tau_hours(
                preset, with_cover=bool(self.options.get(CONF_POOL_HAS_COVER))
            )
        else:
            tau_hours = DEFAULT_TAU_HOURS

        raw_temp = _read_float(self.hass, temp_id)
        data.forecast_value = _read_float(self.hass, forecast_id)

        # Solar coupling — read both sensors (best-effort) regardless of temp
        # mode so the user can see the values in the state attributes.
        solar_power = _read_float(
            self.hass, self.options.get(CONF_SOLAR_POWER_SENSOR)
        )
        # Peak reference priority: explicit installed capacity (stable)
        # beats a sensor like `mptt_*_max_power_today`, which resets at
        # midnight and saturates solar_fraction to ~100% in early morning.
        solar_peak: float | None = None
        solar_installed = self.options.get(CONF_SOLAR_INSTALLED_WATTS)
        if solar_installed is not None:
            try:
                v = float(solar_installed)
                if v > 0:
                    solar_peak = v
            except (TypeError, ValueError):
                pass
        if solar_peak is None:
            solar_peak = _read_float(
                self.hass, self.options.get(CONF_SOLAR_PEAK_SENSOR)
            )
        if solar_power is not None and solar_peak and solar_peak > 0:
            data.solar_fraction = max(0.0, min(1.0, solar_power / solar_peak))
        data.solar_power_w = solar_power
        data.solar_peak_w = solar_peak

        smoothing_h = float(
            self.options.get(
                CONF_SMOOTHING_WINDOW_HOURS, DEFAULT_SMOOTHING_WINDOW_HOURS
            )
        )
        # k_sun priority: explicit user override > physics-derived from
        # preset geometry > generic 0.6 fallback. Forced to 0 when no
        # solar sensor is configured (solar term disabled).
        if not self.options.get(CONF_SOLAR_POWER_SENSOR):
            k_sun = 0.0
        elif self.options.get(CONF_SOLAR_COEFFICIENT) is not None:
            k_sun = float(self.options[CONF_SOLAR_COEFFICIENT])
        else:
            derived = compute_solar_coefficient(preset)
            k_sun = derived if derived is not None else DEFAULT_SOLAR_COEFFICIENT

        data.solar_coefficient_effective = k_sun
        data.tau_hours_effective = tau_hours

        autotune_enabled = bool(
            self.options.get(CONF_AUTOTUNE_ENABLED, DEFAULT_AUTOTUNE_ENABLED)
        )
        # Recompute the offset every tick so it decays smoothly as
        # calibrations age out of the window.
        if autotune_enabled:
            self._recompute_learned_offset()
        else:
            self._learned_offset = 0.0

        if temp_mode == TEMP_MODE_AIR_MODEL and raw_temp is not None:
            data.air_temperature_raw = raw_temp

            # Append to rolling buffer and prune.
            self._air_samples.append((now, raw_temp))
            cutoff = now - timedelta(hours=smoothing_h)
            self._air_samples = [s for s in self._air_samples if s[0] >= cutoff]
            if len(self._air_samples) > self._max_samples:
                self._air_samples = self._air_samples[-self._max_samples:]

            air_smoothed = rolling_mean(
                self._air_samples, timedelta(hours=smoothing_h)
            )
            # If the buffer just started (<5min of history), the smoothed
            # value would be nearly equal to the current reading. That
            # collapses to the v0.4 behaviour ("T_eau = T_air"). Detect
            # this and fall back to the raw reading until we have enough
            # samples to make a useful average.
            if air_smoothed is None:
                air_smoothed = raw_temp
            data.air_temperature_smoothed = air_smoothed

            dt_seconds = (
                (now - self._last_model_update).total_seconds()
                if self._last_model_update
                else 0.0
            )
            self._water_modeled = update_thermal_model(
                self._water_modeled,
                air_smoothed,
                offset=offset,
                tau_hours=tau_hours,
                dt_seconds=dt_seconds,
                solar_fraction=data.solar_fraction,
                solar_coefficient=k_sun,
            )
            self._last_model_update = now
            data.water_modeled_raw = self._water_modeled
            data.temperature_used = (
                self._water_modeled + self._learned_offset
                if self._water_modeled is not None
                else None
            )
        elif temp_mode == TEMP_MODE_WATER:
            # Probe IS the truth — no learned offset applied.
            data.temperature_used = raw_temp
        else:
            # Air mode but air sensor unavailable
            data.air_temperature_raw = None
            data.water_modeled_raw = self._water_modeled
            data.temperature_used = (
                self._water_modeled + self._learned_offset
                if self._water_modeled is not None
                else None
            )

        data.learned_temperature_offset = self._learned_offset
        data.calibration_points = len(self._calibrations)

        pivot = _pivot_for_day(now, pivot_hour)
        if data.temperature_used is not None:
            curve_anchors: list[tuple[float, float]] | None = None
            if bool(
                self.options.get(
                    CONF_DURATION_CURVE_ENABLED, DEFAULT_DURATION_CURVE_ENABLED
                )
            ):
                curve_anchors = [
                    (15.0, float(self.options.get(
                        CONF_DURATION_AT_15C, DEFAULT_DURATION_AT_15C))),
                    (20.0, float(self.options.get(
                        CONF_DURATION_AT_20C, DEFAULT_DURATION_AT_20C))),
                    (25.0, float(self.options.get(
                        CONF_DURATION_AT_25C, DEFAULT_DURATION_AT_25C))),
                    (30.0, float(self.options.get(
                        CONF_DURATION_AT_30C, DEFAULT_DURATION_AT_30C))),
                    (35.0, float(self.options.get(
                        CONF_DURATION_AT_35C, DEFAULT_DURATION_AT_35C))),
                ]
            duration, heatwave = compute_duration(
                data.temperature_used,
                min_hours=min_h,
                max_hours=max_h,
                forecast_value=data.forecast_value,
                heatwave_threshold=heatwave_threshold,
                curve_anchors=curve_anchors,
            )
            # Apply the user-defined global multiplier, then re-clamp
            # to [min_h, max_h] so we don't blow past the bounds the
            # user has set (e.g. multiplier 1.5 capped at max_hours).
            mult = float(
                self.options.get(
                    CONF_FILTRATION_MULTIPLIER, DEFAULT_FILTRATION_MULTIPLIER
                )
            )
            duration = max(min_h, min(max_h, duration * mult))

            data.duration_hours = duration
            data.heatwave_active = heatwave
            raw_runs = build_runs(pivot, duration, break_h)
            # Apply hard time-window bounds. Lets the user say
            # "never before 8h" / "stop by 21h" without breaking the
            # pivot/split symmetry of the scheduling logic.
            data.runs = self._clamp_runs_to_bounds(raw_runs, now)
            data.next_start, data.next_end = self._compute_next_window(data.runs, now)

        pump_id: str = self.options[CONF_PUMP_SWITCH]
        elec_id: str | None = self.options.get(CONF_ELECTROLYZER_SWITCH)
        data.pump_available = self._is_available(pump_id)
        data.electrolyzer_available = (
            self._is_available(elec_id) if elec_id else True
        )
        self._log_availability_transition(pump_id, data.pump_available, "pump")
        if elec_id:
            self._log_availability_transition(
                elec_id, data.electrolyzer_available, "electrolyzer"
            )

        # Backwash timer
        if self._backwash_ends_at is not None and now >= self._backwash_ends_at:
            _LOGGER.info("Backwash cycle ended")
            self._backwash_ends_at = None
        data.backwash_active = self._backwash_ends_at is not None
        data.backwash_ends_at = self._backwash_ends_at

        # Generic routine timer: when it expires, revert to AUTO. Covers
        # the manual maintenance_start workflow and the preset routines.
        if (
            self._mode_timer_ends_at is not None
            and now >= self._mode_timer_ends_at
        ):
            _LOGGER.info(
                "Routine %s ended — reverting to AUTO",
                self._mode_timer_key or "?",
            )
            self._mode_timer_ends_at = None
            self._mode_timer_key = None
            self._mode_timer_dose_info = None
            self.mode = MODE_AUTO
        # Maintenance flag = timer active AND we're physically in MAINTENANCE.
        data.maintenance_active = (
            self._mode_timer_ends_at is not None and self.mode == MODE_MAINTENANCE
        )
        data.maintenance_ends_at = (
            self._mode_timer_ends_at if data.maintenance_active else None
        )
        if self._mode_timer_ends_at is not None:
            data.active_routine = {
                "key": self._mode_timer_key,
                "mode": self.mode,
                "ends_at": self._mode_timer_ends_at.isoformat(),
                "dose_info": self._mode_timer_dose_info,
            }

        # Winterization (month-range check, with optional manual override)
        win_override = self.options.get(
            CONF_WINTERIZATION_OVERRIDE, DEFAULT_WINTERIZATION_OVERRIDE
        )
        if win_override == "on":
            data.winterization_active = True
        elif win_override == "off":
            data.winterization_active = False
        else:
            win_start = int(self.options.get(CONF_WINTERIZATION_START_MONTH, 0) or 0)
            win_end = int(self.options.get(CONF_WINTERIZATION_END_MONTH, 0) or 0)
            data.winterization_active = self._is_winter_month(now, win_start, win_end)

        # Pump short-cycle debounce: update _pump_continuous_on_since
        short_cycle = int(
            self.options.get(
                CONF_PUMP_SHORT_CYCLE_THRESHOLD, DEFAULT_PUMP_SHORT_CYCLE_THRESHOLD
            )
        )
        pump_phys_state = self.hass.states.get(pump_id)
        pump_is_on = (
            pump_phys_state is not None and pump_phys_state.state == STATE_ON
        )
        if pump_is_on:
            if self._pump_continuous_on_since is None:
                # First observation of the pump in this coordinator instance
                # (e.g., after HA restart). Don't restart the post_start
                # timer from scratch — trust the physical switch's
                # last_changed timestamp as the start of the continuous ON
                # period. This avoids forcing the electrolyzer to wait
                # another 120 s every time HA reboots.
                last_changed = getattr(pump_phys_state, "last_changed", None)
                if last_changed is not None:
                    self._pump_continuous_on_since = dt_util.as_local(last_changed)
                elif (
                    self._pump_last_off is not None
                    and (now - self._pump_last_off).total_seconds() < short_cycle
                ):
                    # Brief OFF glitch (short cycle) — preserve the prior
                    # continuous-on start by using the OFF moment.
                    self._pump_continuous_on_since = self._pump_last_off
                else:
                    self._pump_continuous_on_since = now
        else:
            if self._pump_continuous_on_since is not None:
                # Pump just went off
                self._pump_last_off = now
                self._pump_continuous_on_since = None

        pump_target, reason = self._decide_pump(now, data, water_low_id)
        elec_target, elec_block = self._decide_electrolyzer(
            now,
            data,
            post_start=post_start,
            pre_stop=pre_stop,
            elec_min=elec_min,
            elec_max=elec_max,
            short_cycle_threshold=short_cycle,
        )

        data.pump_should_be_on = pump_target
        data.electrolyzer_should_be_on = elec_target
        data.electrolyzer_block_reason = elec_block
        data.reason = reason

        # Per-mode time accounting: count only the seconds during which
        # the pump is actually running. Off → counter stays 0. Auto →
        # only the schedule run window contributes. Marche / Pompe seule
        # / Maintenance → full duration, since the pump is forced on.
        # Backwash gets its own bucket so its contribution doesn't bleed
        # into whatever mode happened to be selected at the time.
        if self._last_mode_tick is not None:
            dt_sec = (now - self._last_mode_tick).total_seconds()
            if 0 < dt_sec < 300:  # guard against gaps > 5 min
                bucket: str | None = None
                if data.backwash_active:
                    bucket = "backwash"
                elif pump_target:
                    bucket = self.mode or MODE_AUTO
                if bucket is not None:
                    self._mode_time_today[bucket] = (
                        self._mode_time_today.get(bucket, 0.0) + dt_sec
                    )
        self._last_mode_tick = now
        data.mode_time_today = dict(self._mode_time_today)

        # UI feature flags (v0.14). The card reads these to decide what
        # to render. The integration logic doesn't depend on them.
        data.has_electrolyzer = bool(self.options.get(CONF_ELECTROLYZER_SWITCH))
        data.show_illustration = bool(
            self.options.get(CONF_SHOW_ILLUSTRATION, DEFAULT_SHOW_ILLUSTRATION)
        )
        data.chemistry_enabled = bool(
            self.options.get(CONF_CHEMISTRY_ENABLED, DEFAULT_CHEMISTRY_ENABLED)
        )

        # Chemistry diagnosis. Skip the computation entirely when the
        # user has turned chemistry off — saves a few CPU cycles each
        # tick and avoids polluting the sensor attributes.
        if data.chemistry_enabled:
            vol = preset["volume_m3"] if preset else None
            data.chemistry, data.chemistry_recommendations = self._build_chemistry_diagnosis(vol)

        if preset is not None:
            svg_state = self._svg_state(pump_target, reason)
            data.pool_svg = render_pool_svg(
                preset,
                state=svg_state,
                temperature=data.temperature_used,
                duration_hours=data.duration_hours,
            )

        # Image URLs for the card to choose from (priority: user > bundled > inline SVG)
        user_url = self.options.get(CONF_POOL_IMAGE_URL)
        if user_url:
            data.pool_image_url = user_url
        if preset is not None:
            shape = preset.get("shape")
            if shape == "round":
                # PNG since v0.13.4 — photorealistic above-ground frame
                # pool illustrations. SVGs kept in the repo as fallback
                # for users with `?legacy_svg=1` in the image URL config.
                data.pool_bundled_url = "/pool_pump_card_assets/illustrations/pool_round.png"
            elif shape == "rect":
                data.pool_bundled_url = "/pool_pump_card_assets/illustrations/pool_rect.png"

        await self._apply_switch(pump_id, pump_target, "pump", reason)
        if elec_id:
            await self._apply_switch(elec_id, elec_target, "electrolyzer", elec_block)

        # Power and energy accounting (best-effort: requires user to
        # configure pump_power_sensor / electrolyzer_power_sensor pointing
        # at smart-plug power readings).
        pump_pw = _read_float(self.hass, self.options.get(CONF_PUMP_POWER_SENSOR))
        elec_pw = _read_float(self.hass, self.options.get(CONF_ELECTROLYZER_POWER_SENSOR))
        data.pump_power_w = pump_pw
        data.electrolyzer_power_w = elec_pw
        if pump_pw is not None or elec_pw is not None:
            data.total_power_w = (pump_pw or 0) + (elec_pw or 0)

            # Riemann integration: kWh += W × dt_h / 1000
            today_key = now.date().isoformat()
            if self._energy_today_date != today_key:
                self._energy_today_kwh = 0.0
                self._energy_today_date = today_key
            if self._last_energy_update is not None:
                dt_h = (now - self._last_energy_update).total_seconds() / 3600
                # Guard against huge dt after long HA downtime
                if 0 < dt_h < 0.5:
                    delta_kwh = data.total_power_w * dt_h / 1000
                    self._energy_today_kwh += delta_kwh
                    self._energy_total_kwh += delta_kwh
            self._last_energy_update = now

        data.energy_today_kwh = self._energy_today_kwh
        data.energy_total_kwh = self._energy_total_kwh

        # Cell-hour accumulator: integrate when cell physically ON
        if elec_id:
            cell_state = self.hass.states.get(elec_id)
            cell_on = cell_state is not None and cell_state.state == STATE_ON
            if cell_on and self._last_cell_update is not None:
                dt_h = (now - self._last_cell_update).total_seconds() / 3600
                if 0 < dt_h < 0.5:
                    self._cell_hours_total += dt_h
            self._last_cell_update = now
        data.cell_hours_total = self._cell_hours_total

        # Persist accumulators every tick. Store batches writes (~10s
        # debounce by HA itself) so this is cheap. Was previously only
        # called inside the air_model branch, which meant users in
        # water-probe mode lost their counters at every restart.
        await self._async_save_model()

        return data

    @staticmethod
    def _svg_state(pump_on: bool, reason: str) -> str:
        if reason == RUN_REASON_MANUAL_OFF:
            return "forced_off"
        if pump_on:
            return "running"
        return "idle"

    def _decide_pump(
        self, now: datetime, data: PoolPumpData, water_low_id: str | None
    ) -> tuple[bool, str]:
        result = self._decide_pump_inner(now, data, water_low_id)
        in_schedule = any(r.contains(now) for r in data.runs)
        runs_str = ", ".join(
            f"{r.start.strftime('%H:%M')}→{r.end.strftime('%H:%M')}" for r in data.runs
        ) or "none"
        _LOGGER.warning(
            "DECIDE_PUMP: mode=%s | now=%s | runs=[%s] | in_schedule=%s | "
            "backwash=%s maint=%s winter=%s | → target=%s reason=%s",
            self.mode,
            now.strftime("%H:%M:%S"),
            runs_str,
            in_schedule,
            data.backwash_active,
            data.maintenance_active,
            data.winterization_active,
            result[0],
            result[1],
        )
        return result

    def _decide_pump_inner(
        self, now: datetime, data: PoolPumpData, water_low_id: str | None
    ) -> tuple[bool, str]:
        # Backwash takes precedence over everything — pump must run.
        if data.backwash_active:
            return True, RUN_REASON_BACKWASH
        # Maintenance (post-dosing) — pump ON, cell OFF.
        if data.maintenance_active or self.mode == MODE_MAINTENANCE:
            return True, RUN_REASON_MAINTENANCE
        # Winterization is the next-highest priority — everything off.
        if data.winterization_active:
            return False, RUN_REASON_WINTERIZATION

        if self.mode == MODE_ON:
            return True, RUN_REASON_MANUAL_ON
        if self.mode == MODE_PUMP_ONLY:
            # Forced pump ON like manual mode, but the cell is blocked
            # in _decide_electrolyzer. Use case: chlorine shock — pump
            # must run continuously to mix the dose, cell off.
            return True, RUN_REASON_PUMP_ONLY
        if self.mode == MODE_OFF:
            return False, RUN_REASON_MANUAL_OFF

        if water_low_id:
            water_state = self.hass.states.get(water_low_id)
            if water_state and water_state.state == STATE_ON:
                return False, RUN_REASON_WATER_LOW

        if data.temperature_used is None:
            return False, RUN_REASON_OFF

        if any(r.contains(now) for r in data.runs):
            return True, RUN_REASON_HEATWAVE if data.heatwave_active else RUN_REASON_AUTO

        return False, RUN_REASON_OFF

    def _decide_electrolyzer(
        self,
        now: datetime,
        data: PoolPumpData,
        *,
        post_start: int,
        pre_stop: int,
        elec_min: float,
        elec_max: float,
        short_cycle_threshold: int,
    ) -> tuple[bool, str]:
        """Decide on the actual physical pump state, never on the intended one.

        Safety invariant: the cell must NEVER be energized unless we can
        confirm water is circulating. Drives:
        - backwash mode → cell forced OFF (only pump runs to flush filter)
        - winterization → everything off
        - debounce: a brief pump-off (< short_cycle_threshold s) does NOT
          reset the post-start timer
        """
        if not self.options.get(CONF_ELECTROLYZER_SWITCH):
            return False, ELEC_BLOCK_NONE
        if data.backwash_active:
            return False, ELEC_BLOCK_BACKWASH
        if data.maintenance_active or self.mode == MODE_MAINTENANCE:
            return False, ELEC_BLOCK_MAINTENANCE
        if data.winterization_active:
            return False, ELEC_BLOCK_WINTERIZATION
        if self.mode == MODE_OFF:
            return False, ELEC_BLOCK_MANUAL
        if self.mode == MODE_PUMP_ONLY:
            return False, ELEC_BLOCK_PUMP_ONLY

        pump_id: str = self.options[CONF_PUMP_SWITCH]
        pump_state = self.hass.states.get(pump_id)
        if pump_state is None or pump_state.state == STATE_UNAVAILABLE:
            return False, ELEC_BLOCK_PUMP_UNAVAILABLE
        if pump_state.state != STATE_ON:
            return False, ELEC_BLOCK_PUMP_OFF

        if data.temperature_used is not None:
            if data.temperature_used < elec_min:
                return False, ELEC_BLOCK_TEMP_LOW
            if data.temperature_used > elec_max:
                return False, ELEC_BLOCK_TEMP_HIGH

        # In manual ON mode the cell follows the pump immediately (no schedule margins).
        if self.mode == MODE_ON:
            return True, ELEC_BLOCK_NONE

        # If the cell is already physically on AND the pump is on, the
        # post-start margin is moot — the safety it guards against (cell
        # energized without water flow) does not apply, because water
        # has been flowing already. Don't force-cycle an established
        # cell off just because our in-memory tracker was reset by a
        # restart.
        elec_id = self.options.get(CONF_ELECTROLYZER_SWITCH)
        cell_already_on = False
        if elec_id is not None:
            cell_state = self.hass.states.get(elec_id)
            cell_already_on = cell_state is not None and cell_state.state == STATE_ON

        # Apply post-start margin via _pump_continuous_on_since (debounced
        # against brief pump cycling). Falls back to the run window logic
        # if continuous_on tracking hasn't built up enough history yet.
        if self._pump_continuous_on_since is not None:
            on_for = (now - self._pump_continuous_on_since).total_seconds()
            if on_for < post_start and not cell_already_on:
                # Wake up exactly when the margin expires so the cell
                # turns ON without waiting for the next 60-second tick.
                self._schedule_deferred_refresh(post_start - on_for + 1)
                return False, ELEC_BLOCK_MARGIN
        elif (
            not _electrolyzer_window_ok(data.runs, now, post_start, pre_stop)
            and not cell_already_on
        ):
            return False, ELEC_BLOCK_MARGIN

        # Pre-stop margin: still gated by the schedule window
        if not _electrolyzer_window_ok(data.runs, now, post_start, pre_stop):
            return False, ELEC_BLOCK_MARGIN

        return True, ELEC_BLOCK_NONE

    def _is_available(self, entity_id: str | None) -> bool:
        if not entity_id:
            return True
        state = self.hass.states.get(entity_id)
        return state is not None and state.state != STATE_UNAVAILABLE

    def _log_availability_transition(
        self, entity_id: str, available: bool, label: str
    ) -> None:
        prev = self._availability_state.get(entity_id)
        if prev is None:
            self._availability_state[entity_id] = available
            return
        if prev != available:
            self._availability_state[entity_id] = available
            if available:
                _LOGGER.info("%s switch %s came back online", label, entity_id)
            else:
                _LOGGER.warning(
                    "%s switch %s went unavailable — output suspended",
                    label,
                    entity_id,
                )

    def _clamp_runs_to_bounds(self, runs: list[Run], now: datetime) -> list[Run]:
        """Clip each run to [earliest_start_hour, latest_end_hour] today.

        Hours are integers 0..24 (24 == midnight next day). Defaults are
        0 and 24 → no clipping. If a run ends up empty after clipping
        (start >= end), it's dropped.
        """
        earliest = int(
            self.options.get(CONF_EARLIEST_START_HOUR, DEFAULT_EARLIEST_START_HOUR)
        )
        latest = int(
            self.options.get(CONF_LATEST_END_HOUR, DEFAULT_LATEST_END_HOUR)
        )
        if earliest <= 0 and latest >= 24:
            return runs

        clamped: list[Run] = []
        for r in runs:
            day = dt_util.as_local(r.start).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            lo = day + timedelta(hours=earliest)
            hi = day + timedelta(hours=latest)
            new_start = max(r.start, lo)
            new_end = min(r.end, hi)
            if new_start < new_end:
                clamped.append(Run(start=new_start, end=new_end))
        return clamped

    @staticmethod
    def _compute_next_window(
        runs: list[Run], now: datetime
    ) -> tuple[datetime | None, datetime | None]:
        if not runs:
            return None, None
        for r in runs:
            if now < r.end:
                return r.start, r.end
        return runs[0].start, runs[-1].end  # today's runs are past

    async def _apply_switch(
        self, entity_id: str, target_on: bool, label: str, reason: str
    ) -> None:
        state = self.hass.states.get(entity_id)
        if state is None or state.state == STATE_UNAVAILABLE:
            _LOGGER.debug("%s switch %s unavailable", label, entity_id)
            return
        is_on = state.state == STATE_ON
        if target_on == is_on:
            return
        # Cooldown: if we already asked for this exact target within
        # SWITCH_REAPPLY_COOLDOWN, the device is flapping (Tuya poll
        # artefact, plug that bounces back, physical override…). Sending
        # turn_off every tick would spam services and fatigue the relay.
        # A *different* target always bypasses the cooldown so a real
        # mode change or scheduled transition takes effect immediately.
        now = dt_util.utcnow()
        last = self._switch_last_action.get(entity_id)
        if last is not None:
            last_at, last_target = last
            if last_target == target_on and now - last_at < SWITCH_REAPPLY_COOLDOWN:
                _LOGGER.warning(
                    "%s %s: same target (%s) requested %ss ago, skipping "
                    "(reason: %s). Device is flapping — check the plug's "
                    "poll/reporting behaviour.",
                    label,
                    entity_id,
                    "on" if target_on else "off",
                    int((now - last_at).total_seconds()),
                    reason,
                )
                return
        service = "turn_on" if target_on else "turn_off"
        _LOGGER.warning(
            "APPLY_SWITCH_CALL: %s %s → %s | was=%s | mode=%s | reason=%s",
            label,
            entity_id,
            service,
            "on" if is_on else "off",
            self.mode,
            reason,
        )
        self._switch_last_action[entity_id] = (now, target_on)
        self._debug_last_call[entity_id] = (now, service, reason)
        await self.hass.services.async_call(
            "switch", service, {"entity_id": entity_id}, blocking=False
        )

    @callback
    def _debug_on_switch_change(self, event) -> None:
        """v0.16.5 debug: log every state change on watched switches with
        the event's context and correlation with our own last command.
        If a change happens WITHOUT a matching APPLY_SWITCH_CALL in the
        last ~10 seconds, the change came from OUTSIDE this integration.
        """
        entity_id = event.data.get("entity_id")
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        ctx = event.context
        old_s = old.state if old else "None"
        new_s = new.state if new else "None"
        if old_s == new_s:
            return
        now = dt_util.utcnow()
        last = self._debug_last_call.get(entity_id)
        if last is not None:
            last_at, last_service, last_reason = last
            age = (now - last_at).total_seconds()
            expected = "on" if last_service == "turn_on" else "off"
            if age <= 10 and new_s == expected:
                origin = f"US ({age:.1f}s ago, service={last_service}, reason={last_reason})"
            elif age <= 10:
                origin = (
                    f"UNEXPECTED — we called {last_service} {age:.1f}s ago (reason={last_reason}) "
                    f"but state moved to {new_s}"
                )
            else:
                origin = (
                    f"EXTERNAL — our last call was {last_service} {age:.1f}s ago "
                    f"(too old to be us)"
                )
        else:
            origin = "EXTERNAL — we never touched this entity"
        _LOGGER.warning(
            "PUMP_STATE_CHANGE: %s %s→%s | ctx.id=%s user_id=%s parent_id=%s | mode=%s | origin=%s",
            entity_id,
            old_s,
            new_s,
            ctx.id if ctx else None,
            ctx.user_id if ctx else None,
            ctx.parent_id if ctx else None,
            self.mode,
            origin,
        )
