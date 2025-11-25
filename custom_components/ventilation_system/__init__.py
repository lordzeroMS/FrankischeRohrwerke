from __future__ import annotations

import asyncio
from datetime import time as dt_time
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol
from aiohttp import FormData
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_IP_ADDRESS,
    DATA_COORDINATOR,
    DOMAIN,
    PLATFORMS,
    SERVICE_SET_BYPASS_MODE,
    SERVICE_SET_STAGE,
    SERVICE_SET_WEEK_PROGRAM,
)
from .coordinator import VentilationDataCoordinator

BYPASS_MODES = {
    "manual_open": "bypa0",
    "manual_close": "bypa1",
    "auto": "bypa2",
}

WEEKDAY_VALUE = {
    "mon": "1",
    "tue": "2",
    "wed": "3",
    "thu": "4",
    "fri": "5",
    "sat": "6",
    "sun": "7",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    coordinator = VentilationDataCoordinator(hass, entry.data[CONF_IP_ADDRESS])
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        CONF_IP_ADDRESS: entry.data[CONF_IP_ADDRESS],
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.data[DOMAIN].get("services_registered"):
        _register_services(hass)
        hass.data[DOMAIN]["services_registered"] = True

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STAGE,
        lambda call: _async_handle_set_stage(hass, call),
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_id,
                vol.Required("stage"): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BYPASS_MODE,
        lambda call: _async_handle_set_bypass_mode(hass, call),
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_id,
                vol.Required("mode"): vol.In(list(BYPASS_MODES)),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_WEEK_PROGRAM,
        lambda call: _async_handle_set_week_program(hass, call),
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_id,
                vol.Required("program"): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=10)
                ),
                vol.Required("stage"): vol.All(vol.Coerce(int), vol.Range(min=1, max=3)),
                vol.Required("start"): cv.time,
                vol.Required("stop"): cv.time,
                vol.Required("days"): vol.All(
                    cv.ensure_list,
                    [
                        vol.Any(
                            vol.All(str, vol.Lower, vol.In(list(WEEKDAY_VALUE))),
                            vol.All(vol.Coerce(int), vol.In(range(1, 8))),
                        )
                    ],
                ),
            }
        ),
    )


def _async_get_entry_runtime_data(hass: HomeAssistant, entity_id: str) -> dict[str, Any]:
    registry = er.async_get(hass)
    entity_entry = registry.async_get(entity_id)
    if not entity_entry or not entity_entry.config_entry_id:
        raise HomeAssistantError(
            f"Entity {entity_id} is not associated with a ventilation system entry"
        )
    entry_data = hass.data[DOMAIN].get(entity_entry.config_entry_id)
    if not entry_data:
        raise HomeAssistantError(
            f"Config entry {entity_entry.config_entry_id} is not loaded"
        )
    return entry_data


async def _async_handle_set_stage(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_data = _async_get_entry_runtime_data(hass, call.data[ATTR_ENTITY_ID])
    stage = call.data["stage"]
    await _async_request(
        hass,
        entry_data[CONF_IP_ADDRESS],
        "GET",
        f"/stufe.cgi?stufe={stage}",
    )
    await entry_data[DATA_COORDINATOR].async_request_refresh()


async def _async_handle_set_bypass_mode(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_data = _async_get_entry_runtime_data(hass, call.data[ATTR_ENTITY_ID])
    mode = call.data["mode"]
    form = FormData()
    form.add_field("bypassSt", BYPASS_MODES[mode])
    await _async_request(hass, entry_data[CONF_IP_ADDRESS], "POST", "/setup.htm", form)
    await entry_data[DATA_COORDINATOR].async_request_refresh()


async def _async_handle_set_week_program(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_data = _async_get_entry_runtime_data(hass, call.data[ATTR_ENTITY_ID])
    program = call.data["program"]
    stage = call.data["stage"]
    start: dt_time = call.data["start"]
    stop: dt_time = call.data["stop"]
    day_values = _normalize_weekdays(call.data["days"])
    form = _build_week_program_payload(program, stage, start, stop, day_values)
    await _async_request(hass, entry_data[CONF_IP_ADDRESS], "POST", "/wopla.htm", form)
    await entry_data[DATA_COORDINATOR].async_request_refresh()


def _normalize_weekdays(raw_days: list[Any]) -> list[str]:
    normalized: list[str] = []
    for item in raw_days:
        if isinstance(item, int):
            normalized.append(str(item))
            continue
        normalized.append(WEEKDAY_VALUE[item.lower()])
    return normalized


def _build_week_program_payload(
    program: int, stage: int, start: dt_time, stop: dt_time, day_values: list[str]
) -> FormData:
    p_value = 0 if program == 10 else program
    start_hour = f"{start.hour:02d}"
    start_minute = f"{start.minute:02d}"
    stop_hour = f"{stop.hour:02d}"
    stop_minute = f"{stop.minute:02d}"

    selections = ["0"] * 7
    for day in day_values:
        idx = int(day) - 1
        if idx < 0 or idx > 6:
            continue
        selections[idx] = day

    form = FormData()
    form.add_field(
        "progsubmit",
        f"P{p_value}S{stage}AH{start_hour}AM{start_minute}EH{stop_hour}EM{stop_minute}W{''.join(selections)}",
    )
    form.add_field("prog", str(program))
    form.add_field("progstu", str(stage))
    form.add_field("progstartH", start_hour)
    form.add_field("progstartM", start_minute)
    form.add_field("progstopH", stop_hour)
    form.add_field("progstopM", stop_minute)
    for day in day_values:
        form.add_field("wota", day)
    return form


async def _async_request(
    hass: HomeAssistant,
    host: str,
    method: str,
    path: str,
    data: FormData | None = None,
) -> None:
    url = f"http://{host}{path}"
    session = async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(15):
            if method == "POST":
                response = await session.post(url, data=data)
            else:
                response = await session.get(url)
            response.raise_for_status()
    except asyncio.TimeoutError as err:
        raise HomeAssistantError(f"Timeout while contacting {url}") from err
    except aiohttp.ClientResponseError as err:
        raise HomeAssistantError(f"Request to {url} failed: {err.status}") from err
    except aiohttp.ClientError as err:
        raise HomeAssistantError(f"Could not call {url}: {err}") from err
