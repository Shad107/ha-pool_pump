"""Constants for Pool Pump Manager."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "pool_pump"
NAME = "Pool Pump Manager"
VERSION = "0.11.1"
INTEGRATION_VERSION = VERSION

URL_BASE = "/pool_pump_card_assets"
JSMODULES = [
    {"name": "Pool Pump Card", "filename": "pool-pump-card.js", "version": VERSION},
]

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
CONF_SMOOTHING_WINDOW_HOURS = "smoothing_window_hours"
CONF_SOLAR_POWER_SENSOR = "solar_power_sensor"
CONF_SOLAR_PEAK_SENSOR = "solar_peak_sensor"
CONF_SOLAR_INSTALLED_WATTS = "solar_installed_watts"
CONF_SOLAR_COEFFICIENT = "solar_coefficient"
CONF_PUMP_POWER_SENSOR = "pump_power_sensor"
CONF_ELECTROLYZER_POWER_SENSOR = "electrolyzer_power_sensor"
CONF_WINTERIZATION_START_MONTH = "winterization_start_month"
CONF_WINTERIZATION_END_MONTH = "winterization_end_month"
CONF_POOL_IMAGE_URL = "pool_image_url"
CONF_BACKWASH_DURATION_MINUTES = "backwash_duration_minutes"
CONF_PUMP_SHORT_CYCLE_THRESHOLD = "pump_short_cycle_threshold"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_AUTOTUNE_ENABLED = "autotune_enabled"
CONF_AUTOTUNE_WINDOW_DAYS = "autotune_window_days"

# Chemistry parameters: each can be sourced from a user-provided sensor
# (auto-measuring device like Ondilo, Flipr, Blue Riiot) or from the
# number entity we create ourselves for manual entry. Both paths feed
# the same diagnosis logic.
CONF_CHEM_PH_SENSOR = "chem_ph_sensor"
CONF_CHEM_FREE_CHLORINE_SENSOR = "chem_free_chlorine_sensor"
CONF_CHEM_TOTAL_CHLORINE_SENSOR = "chem_total_chlorine_sensor"
CONF_CHEM_TAC_SENSOR = "chem_tac_sensor"
CONF_CHEM_TH_SENSOR = "chem_th_sensor"
CONF_CHEM_CYA_SENSOR = "chem_cya_sensor"
CONF_CHEM_SALT_SENSOR = "chem_salt_sensor"
CONF_CHEM_ORP_SENSOR = "chem_orp_sensor"

DEFAULT_BACKWASH_DURATION_MINUTES = 5
DEFAULT_PUMP_SHORT_CYCLE_THRESHOLD = 30  # seconds; brief pump off ignored
DEFAULT_AUTOTUNE_ENABLED = True
DEFAULT_AUTOTUNE_WINDOW_DAYS = 30
DEFAULT_AUTOTUNE_MAX_OFFSET = 5.0  # safety clamp, °C
DEFAULT_AUTOTUNE_HALF_LIFE_DAYS = 7.0  # newer calibrations weighted more
DEFAULT_FORECAST_PREHEAT_THRESHOLD = 18.0  # °C; below this tomorrow → longer today

# Chemistry parameter metadata.
# Each entry: (key, label_fr, unit, min, max, step, default_target,
#              target_low, target_high, enabled_by_default)
CHEM_PARAMS = [
    # key,              label,                unit,   min,   max,   step,  tgt,   low,    high,   default_on
    ("ph",              "pH",                 "pH",   0.0,   14.0,  0.1,   7.4,   7.2,    7.6,    True),
    ("free_chlorine",   "Chlore libre",       "ppm",  0.0,   20.0,  0.1,   2.0,   1.0,    3.0,    True),
    ("total_chlorine",  "Chlore total",       "ppm",  0.0,   20.0,  0.1,   2.0,   1.0,    3.5,    True),
    ("tac",             "Alcalinité (TAC)",   "ppm",  0.0,   300.0, 10.0,  100.0, 80.0,   120.0,  True),
    ("th",              "Dureté (TH)",        "ppm",  0.0,   1000.0,10.0,  200.0, 100.0,  300.0,  False),
    ("cya",             "Stabilisant (CYA)",  "ppm",  0.0,   300.0, 5.0,   40.0,  30.0,   50.0,   False),
    ("salt",            "Sel",                "ppm",  0.0,   6000.0,50.0,  4000.0,3000.0, 5000.0, False),
    ("orp",             "ORP (rédox)",        "mV",   0.0,   1000.0,10.0,  700.0, 650.0,  750.0,  False),
]

# Maintenance mode: pump forced ON + cell forced OFF for a duration,
# then auto-revert to MODE_AUTO. Used after chemical dosing to mix.
MODE_MAINTENANCE = "maintenance"

DEFAULT_SMOOTHING_WINDOW_HOURS = 24.0
DEFAULT_SOLAR_COEFFICIENT = 0.6  # °C / hour at full sun (P_solar = P_peak)

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
MODE_PUMP_ONLY = "pump_only"
MODE_OPTIONS = [MODE_AUTO, MODE_ON, MODE_PUMP_ONLY, MODE_OFF, MODE_MAINTENANCE]

RUN_REASON_OFF = "off"
RUN_REASON_AUTO = "auto"
RUN_REASON_MANUAL_ON = "manual_on"
RUN_REASON_MANUAL_OFF = "manual_off"
RUN_REASON_WATER_LOW = "water_low"
RUN_REASON_HEATWAVE = "heatwave"
RUN_REASON_BACKWASH = "backwash"
RUN_REASON_WINTERIZATION = "winterization"
RUN_REASON_PUMP_ONLY = "pump_only"
RUN_REASON_MAINTENANCE = "maintenance"

ELEC_BLOCK_NONE = "none"
ELEC_BLOCK_PUMP_OFF = "pump_off"
ELEC_BLOCK_PUMP_UNAVAILABLE = "pump_unavailable"
ELEC_BLOCK_MARGIN = "margin"
ELEC_BLOCK_TEMP_LOW = "temp_low"
ELEC_BLOCK_TEMP_HIGH = "temp_high"
ELEC_BLOCK_MANUAL = "manual"
ELEC_BLOCK_BACKWASH = "backwash"
ELEC_BLOCK_WINTERIZATION = "winterization"
ELEC_BLOCK_PUMP_ONLY = "pump_only"
ELEC_BLOCK_MAINTENANCE = "maintenance"
