from __future__ import annotations

from logging import getLogger
from homeassistant.const import Platform


LOGGER = getLogger(__package__)

DOMAIN = "ventilation_system"
CONF_IP_ADDRESS = "ip_address"
DATA_COORDINATOR = "coordinator"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.BINARY_SENSOR]

SERVICE_SET_STAGE = "set_stage"
SERVICE_SET_WEEK_PROGRAM = "set_week_program"
SERVICE_SET_BYPASS_MODE = "set_bypass_mode"
