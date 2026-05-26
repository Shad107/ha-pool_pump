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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    COLD_THRESHOLD_CELSIUS,
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
    CONF_POOL_PRESET,
    CONF_PUMP_POWER_SENSOR,
    CONF_PUMP_SHORT_CYCLE_THRESHOLD,
    CONF_PUMP_SWITCH,
    CONF_WINTERIZATION_END_MONTH,
    CONF_WINTERIZATION_START_MONTH,
    CONF_SMOOTHING_WINDOW_HOURS,
    CONF_SOLAR_COEFFICIENT,
    CONF_SOLAR_PEAK_SENSOR,
    CONF_SOLAR_POWER_SENSOR,
    CONF_TAU_HOURS,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_OFFSET,
    CONF_TEMPERATURE_SENSOR,
    CONF_WATER_LEVEL_CRITICAL,
    DEFAULT_BACKWASH_DURATION_MINUTES,
    DEFAULT_ELECTROLYZER_MAX_TEMP,
    DEFAULT_ELECTROLYZER_MIN_TEMP,
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
    ELEC_BLOCK_USER_DISABLED,
    ELEC_BLOCK_WINTERIZATION,
    MODE_AUTO,
    MODE_OFF,
    MODE_ON,
    RUN_REASON_AUTO,
    RUN_REASON_BACKWASH,
    RUN_REASON_HEATWAVE,
    RUN_REASON_MANUAL_OFF,
    RUN_REASON_MANUAL_ON,
    RUN_REASON_OFF,
    RUN_REASON_WATER_LOW,
    RUN_REASON_WINTERIZATION,
    STORAGE_KEY_TEMPLATE,
    STORAGE_VERSION,
    TEMP_MODE_AIR_MODEL,
    TEMP_MODE_WATER,
    UPDATE_INTERVAL,
)
from .presets import (
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
    pump_available: bool = True
    electrolyzer_available: bool = True
    air_temperature_smoothed: float | None = None
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


def compute_duration(
    temperature: float,
    *,
    min_hours: float,
    max_hours: float,
    forecast_value: float | None,
    heatwave_threshold: float,
) -> tuple[float, bool]:
    """Return (duration_hours, heatwave_active) for the given inputs."""
    if temperature < COLD_THRESHOLD_CELSIUS:
        base = temperature / 3.0
    else:
        base = temperature / 2.0

    heatwave_active = (
        forecast_value is not None and forecast_value >= heatwave_threshold
    )
    if heatwave_active:
        return max_hours, True

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
        # User-controlled electrolyzer enable flag (independent of pump
        # mode). Off ⇒ cell blocked even if pump is running. Use case:
        # chlorine shock treatment — pump runs to mix the shock dose,
        # cell stays off to avoid over-chlorination.
        self._electrolyzer_enabled: bool = True

    async def async_load_persisted(self) -> None:
        """Load the modeled water temp + air samples from disk (once at init)."""
        stored = await self._store.async_load()
        if not stored:
            return
        self._water_modeled = stored.get("water_temp")
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
        # User-controlled cell enable
        if "electrolyzer_enabled" in stored:
            self._electrolyzer_enabled = bool(stored.get("electrolyzer_enabled"))

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
                "electrolyzer_enabled": self._electrolyzer_enabled,
            }
        )

    def set_electrolyzer_enabled(self, enabled: bool) -> None:
        """User-toggle for the electrolyzer, independent of pump mode."""
        self._electrolyzer_enabled = bool(enabled)
        self.hass.async_create_task(self.async_request_refresh())

    @property
    def electrolyzer_enabled(self) -> bool:
        return self._electrolyzer_enabled

    def set_mode(self, mode: str) -> None:
        """Change manual mode and force a refresh."""
        self.mode = mode
        self.hass.async_create_task(self.async_request_refresh())

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

    async def _async_update_data(self) -> PoolPumpData:
        now = dt_util.now()
        data = PoolPumpData(mode=self.mode)

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
            await self._async_save_model()
            data.temperature_used = self._water_modeled
        elif temp_mode == TEMP_MODE_WATER:
            data.temperature_used = raw_temp
        else:
            # Air mode but air sensor unavailable
            data.air_temperature_raw = None
            data.temperature_used = self._water_modeled  # last known modeled value

        pivot = _pivot_for_day(now, pivot_hour)
        if data.temperature_used is not None:
            duration, heatwave = compute_duration(
                data.temperature_used,
                min_hours=min_h,
                max_hours=max_h,
                forecast_value=data.forecast_value,
                heatwave_threshold=heatwave_threshold,
            )
            data.duration_hours = duration
            data.heatwave_active = heatwave
            data.runs = build_runs(pivot, duration, break_h)
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

        # Winterization (month-range check)
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
                # Coming back from OFF — check if it was a short cycle
                if (
                    self._pump_last_off is not None
                    and (now - self._pump_last_off).total_seconds() < short_cycle
                ):
                    # Brief glitch: keep the prior continuous_on_since if any.
                    # We restore from the same instant minus a tiny offset so
                    # the elapsed time is preserved.
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

        if preset is not None:
            svg_state = self._svg_state(pump_target, reason)
            data.pool_svg = render_pool_svg(
                preset,
                state=svg_state,
                temperature=data.temperature_used,
                duration_hours=data.duration_hours,
            )

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
        # Backwash takes precedence over everything — pump must run.
        if data.backwash_active:
            return True, RUN_REASON_BACKWASH
        # Winterization is the next-highest priority — everything off.
        if data.winterization_active:
            return False, RUN_REASON_WINTERIZATION

        if self.mode == MODE_ON:
            return True, RUN_REASON_MANUAL_ON
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
        if not self._electrolyzer_enabled:
            return False, ELEC_BLOCK_USER_DISABLED
        if data.backwash_active:
            return False, ELEC_BLOCK_BACKWASH
        if data.winterization_active:
            return False, ELEC_BLOCK_WINTERIZATION
        if self.mode == MODE_OFF:
            return False, ELEC_BLOCK_MANUAL

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

        # Apply post-start margin via _pump_continuous_on_since (debounced
        # against brief pump cycling). Falls back to the run window logic
        # if continuous_on tracking hasn't built up enough history yet.
        if self._pump_continuous_on_since is not None:
            on_for = (now - self._pump_continuous_on_since).total_seconds()
            if on_for < post_start:
                return False, ELEC_BLOCK_MARGIN
        elif not _electrolyzer_window_ok(data.runs, now, post_start, pre_stop):
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
        service = "turn_on" if target_on else "turn_off"
        _LOGGER.info("%s %s → %s (reason: %s)", label, entity_id, service, reason)
        await self.hass.services.async_call(
            "switch", service, {"entity_id": entity_id}, blocking=False
        )
