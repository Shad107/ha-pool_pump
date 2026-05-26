"""Constants for Pool Pump Manager."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "pool_pump"
NAME = "Pool Pump Manager"
VERSION = "0.3.3"

ISSUE_URL = "https://github.com/Shad107/ha-pool_pump/issues"

CONF_PUMP_SWITCH = "pump_switch"
CONF_TEMPERATURE_MODE = "temperature_mode"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_TAU_HOURS = "tau_hours"
CONF_TEMPERATURE_OFFSET = "temperature_offset"
CONF_POOL_PRESET = "pool_preset"
CONF_POOL_HAS_COVER = "pool_has_cover"
CONF_MIN_HOURS = "min_hours"
CONF_MAX_HOURS = "max_hours"
CONF_BREAK_HOURS = "break_hours"
CONF_PIVOT_HOUR = "pivot_hour"
CONF_FORECAST_SENSOR = "forecast_sensor"
CONF_HEATWAVE_THRESHOLD = "heatwave_threshold"
CONF_ELECTROLYZER_SWITCH = "electrolyzer_switch"
CONF_ELECTROLYZER_POST_START_DELAY = "electrolyzer_post_start_delay"
CONF_ELECTROLYZER_PRE_STOP_DELAY = "electrolyzer_pre_stop_delay"
CONF_ELECTROLYZER_MIN_TEMP = "electrolyzer_min_temp"
CONF_ELECTROLYZER_MAX_TEMP = "electrolyzer_max_temp"
CONF_WATER_LEVEL_CRITICAL = "water_level_critical"

TEMP_MODE_WATER = "water"
TEMP_MODE_AIR_MODEL = "air_model"
TEMP_MODE_OPTIONS = [TEMP_MODE_WATER, TEMP_MODE_AIR_MODEL]

DEFAULT_TEMPERATURE_MODE = TEMP_MODE_WATER
DEFAULT_TAU_HOURS = 36.0
DEFAULT_TEMPERATURE_OFFSET = 0.0
DEFAULT_MIN_HOURS = 2.0
DEFAULT_MAX_HOURS = 24.0
DEFAULT_BREAK_HOURS = 0.0
DEFAULT_PIVOT_HOUR = 14
DEFAULT_HEATWAVE_THRESHOLD = 28.0
DEFAULT_ELECTROLYZER_POST_START_DELAY = 120
DEFAULT_ELECTROLYZER_PRE_STOP_DELAY = 60
DEFAULT_ELECTROLYZER_MIN_TEMP = 15.0
DEFAULT_ELECTROLYZER_MAX_TEMP = 40.0

COLD_THRESHOLD_CELSIUS = 13.0

UPDATE_INTERVAL = timedelta(minutes=1)

STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = "pool_pump.{entry_id}.water_model"

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

ELEC_BLOCK_NONE = "none"
ELEC_BLOCK_PUMP_OFF = "pump_off"
ELEC_BLOCK_PUMP_UNAVAILABLE = "pump_unavailable"
ELEC_BLOCK_MARGIN = "margin"
ELEC_BLOCK_TEMP_LOW = "temp_low"
ELEC_BLOCK_TEMP_HIGH = "temp_high"
ELEC_BLOCK_MANUAL = "manual"
