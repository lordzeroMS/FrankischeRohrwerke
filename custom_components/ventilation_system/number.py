from __future__ import annotations

import asyncio

import aiohttp
import async_timeout
from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_IP_ADDRESS, DATA_COORDINATOR, DOMAIN
from .coordinator import VentilationDataCoordinator
from .parser import stage_value


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: VentilationDataCoordinator = entry_data[DATA_COORDINATOR]
    async_add_entities(
        [
            VentilationSystemControl(
                coordinator, entry.entry_id, entry.data[CONF_IP_ADDRESS]
            )
        ]
    )


class VentilationSystemControl(
    CoordinatorEntity[VentilationDataCoordinator], NumberEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VentilationDataCoordinator,
        entry_id: str,
        ip_address: str,
    ) -> None:
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._attr_name = "Stage"
        self._attr_unique_id = f"{entry_id}_stage_control"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 4
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.POWER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Fraenkische Ventilation",
            manufacturer="Fraenkische Rohrwerke",
            model="profi-air",
            configuration_url=f"http://{ip_address}/",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        stage = self._current_stage()
        if stage is not None:
            self._attr_native_value = stage

    def _current_stage(self) -> int | None:
        data = self.coordinator.data
        if not data:
            return None
        return stage_value(data.get("aktuell0"))

    async def async_set_native_value(self, value: float) -> None:
        stage = int(value)
        await _async_call_stage_endpoint(self.hass, self._ip_address, stage)
        self._attr_native_value = stage
        await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        stage = self._current_stage()
        if stage is not None:
            self._attr_native_value = stage


async def _async_call_stage_endpoint(
    hass: HomeAssistant, host: str, stage: int
) -> None:
    session = async_get_clientsession(hass)
    url = f"http://{host}/stufe.cgi?stufe={stage}"
    try:
        async with async_timeout.timeout(15):
            response = await session.get(url)
            response.raise_for_status()
    except asyncio.TimeoutError as err:
        raise HomeAssistantError(f"Timeout calling {url}") from err
    except aiohttp.ClientError as err:
        raise HomeAssistantError(f"Stage request failed: {err}") from err
