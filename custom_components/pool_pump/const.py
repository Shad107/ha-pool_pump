"""Constants for Pool Pump Manager."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "pool_pump"
NAME = "Pool Pump Manager"
VERSION = "0.1.0"

ISSUE_URL = "https://github.com/Shad107/ha-pool_pump/issues"

CONF_PUMP_SWITCH = "pump_switch"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_TEMPERATURE_KIND = "temperature_kind"
CONF_MIN_HOURS = "min_hours"
CONF_MAX_HOURS = "max_hours"
CONF_BREAK_HOURS = "break_hours"
CONF_PIVOT_HOUR = "pivot_hour"
CONF_FORECAST_SENSOR = "forecast_sensor"
CONF_HEATWAVE_THRESHOLD = "heatwave_threshold"
CONF_ELECTROLYZER_SWITCH = "electrolyzer_switch"
CONF_ELECTROLYZER_POST_START_DELAY = "electrolyzer_post_start_delay"
CONF_ELECTROLYZER_PRE_STOP_DELAY = "electrolyzer_pre_stop_delay"
CONF_WATER_LEVEL_CRITICAL = "water_level_critical"

TEMP_KIND_WATER = "water"
TEMP_KIND_AIR = "air"

DEFAULT_MIN_HOURS = 2.0
DEFAULT_MAX_HOURS = 24.0
DEFAULT_BREAK_HOURS = 0.0
DEFAULT_PIVOT_HOUR = 14
DEFAULT_HEATWAVE_THRESHOLD = 28.0
DEFAULT_ELECTROLYZER_POST_START_DELAY = 120
DEFAULT_ELECTROLYZER_PRE_STOP_DELAY = 60

COLD_THRESHOLD_CELSIUS = 13.0

UPDATE_INTERVAL = timedelta(minutes=1)

MODE_AUTO = "auto"
MODE_ON = "on"
MODE_OFF = "off"
MODE_OPTIONS = [MODE_AUTO, MODE_ON, MODE_OFF]

RUN_REASON_OFF = "off"
RUN_REASON_AUTO = "auto"
RUN_REASON_MANUAL_ON = "manual_on"
RUN_REASON_MANUAL_OFF = "manual_off"
RUN_REASON_WATER_LOW = "water_low"
RUN_REASON_HEATWAVE = "heatwave"
