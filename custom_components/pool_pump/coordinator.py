"""DataUpdateCoordinator for Pool Pump Manager.

Schedule logic (no external lib):
  - total_hours = T/2 (or T/3 below 13°C), clamped to [min_hours, max_hours]
  - if a forecast max sensor is configured and forecast >= heatwave_threshold,
    total_hours is forced to max_hours
  - the run is centered on the configured pivot hour (default 14:00 local),
    optionally split into two runs with a break in the middle

Pump and electrolyzer states are derived from the schedule at every tick;
no delayed callbacks. The electrolyzer is on when the pump has been running
for at least post_start_delay AND will keep running for at least pre_stop_delay.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    COLD_THRESHOLD_CELSIUS,
    CONF_BREAK_HOURS,
    CONF_ELECTROLYZER_POST_START_DELAY,
    CONF_ELECTROLYZER_PRE_STOP_DELAY,
    CONF_ELECTROLYZER_SWITCH,
    CONF_FORECAST_SENSOR,
    CONF_HEATWAVE_THRESHOLD,
    CONF_MAX_HOURS,
    CONF_MIN_HOURS,
    CONF_PIVOT_HOUR,
    CONF_PUMP_SWITCH,
    CONF_TEMPERATURE_SENSOR,
    CONF_WATER_LEVEL_CRITICAL,
    DOMAIN,
    MODE_AUTO,
    MODE_OFF,
    MODE_ON,
    RUN_REASON_AUTO,
    RUN_REASON_HEATWAVE,
    RUN_REASON_MANUAL_OFF,
    RUN_REASON_MANUAL_ON,
    RUN_REASON_OFF,
    RUN_REASON_WATER_LOW,
    UPDATE_INTERVAL,
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
    forecast_value: float | None = None
    duration_hours: float = 0.0
    runs: list[Run] = field(default_factory=list)
    next_start: datetime | None = None
    next_end: datetime | None = None
    pump_should_be_on: bool = False
    electrolyzer_should_be_on: bool = False
    reason: str = RUN_REASON_OFF
    mode: str = MODE_AUTO
    heatwave_active: bool = False


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


def _electrolyzer_target(
    runs: list[Run], now: datetime, post_start: int, pre_stop: int
) -> bool:
    """True iff `now` falls inside a run, with the post-start and pre-stop margins applied."""
    post_start_td = timedelta(seconds=post_start)
    pre_stop_td = timedelta(seconds=pre_stop)
    for r in runs:
        if r.start + post_start_td <= now < r.end - pre_stop_td:
            return True
    return False


class PoolPumpCoordinator(DataUpdateCoordinator[PoolPumpData]):
    """Compute schedule and drive the pump and electrolyzer switches."""

    def __init__(self, hass: HomeAssistant, entry_id: str, options: dict[str, Any]) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.entry_id = entry_id
        self.options = options
        self.mode: str = MODE_AUTO

    def set_mode(self, mode: str) -> None:
        """Change the manual mode and force a refresh."""
        self.mode = mode
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> PoolPumpData:
        now = dt_util.now()
        data = PoolPumpData(mode=self.mode)

        temp_id: str = self.options[CONF_TEMPERATURE_SENSOR]
        forecast_id: str | None = self.options.get(CONF_FORECAST_SENSOR)
        water_low_id: str | None = self.options.get(CONF_WATER_LEVEL_CRITICAL)

        min_h = float(self.options.get(CONF_MIN_HOURS, 2.0))
        max_h = float(self.options.get(CONF_MAX_HOURS, 24.0))
        break_h = float(self.options.get(CONF_BREAK_HOURS, 0.0))
        pivot_hour = int(self.options.get(CONF_PIVOT_HOUR, 14))
        heatwave_threshold = float(self.options.get(CONF_HEATWAVE_THRESHOLD, 28.0))
        post_start = int(self.options.get(CONF_ELECTROLYZER_POST_START_DELAY, 120))
        pre_stop = int(self.options.get(CONF_ELECTROLYZER_PRE_STOP_DELAY, 60))

        temp = _read_float(self.hass, temp_id)
        forecast = _read_float(self.hass, forecast_id)
        data.temperature_used = temp
        data.forecast_value = forecast

        # Always compute the day's schedule for visibility, even if we end up off.
        pivot = _pivot_for_day(now, pivot_hour)
        if temp is not None:
            duration, heatwave = compute_duration(
                temp,
                min_hours=min_h,
                max_hours=max_h,
                forecast_value=forecast,
                heatwave_threshold=heatwave_threshold,
            )
            data.duration_hours = duration
            data.heatwave_active = heatwave
            data.runs = build_runs(pivot, duration, break_h)
            data.next_start, data.next_end = self._compute_next_window(data.runs, now)

        # Decide pump + electrolyzer targets
        pump_target, reason = self._decide_pump(now, data, water_low_id)
        elec_target = (
            pump_target
            and bool(self.options.get(CONF_ELECTROLYZER_SWITCH))
            and self.mode != MODE_OFF
            and (
                self.mode == MODE_ON
                or _electrolyzer_target(data.runs, now, post_start, pre_stop)
            )
        )

        data.pump_should_be_on = pump_target
        data.electrolyzer_should_be_on = elec_target
        data.reason = reason

        await self._apply_switch(self.options[CONF_PUMP_SWITCH], pump_target, "pump", reason)
        elec_id = self.options.get(CONF_ELECTROLYZER_SWITCH)
        if elec_id:
            await self._apply_switch(elec_id, elec_target, "electrolyzer", reason)

        return data

    def _decide_pump(
        self, now: datetime, data: PoolPumpData, water_low_id: str | None
    ) -> tuple[bool, str]:
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

    @staticmethod
    def _compute_next_window(
        runs: list[Run], now: datetime
    ) -> tuple[datetime | None, datetime | None]:
        if not runs:
            return None, None
        for r in runs:
            if now < r.end:
                return r.start, r.end
        return runs[0].start, runs[-1].end  # today's runs are past, show last as reference

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
