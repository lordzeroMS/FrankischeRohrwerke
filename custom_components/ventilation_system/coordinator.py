from __future__ import annotations

import asyncio
from datetime import timedelta

import aiohttp
import async_timeout
import xmltodict
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER


class VentilationDataCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Fetch data from the ventilation controller."""

    def __init__(self, hass: HomeAssistant, ip_address: str) -> None:
        self._ip_address = ip_address
        super().__init__(
            hass,
            LOGGER,
            name=f"Ventilation system ({ip_address})",
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self) -> dict[str, str]:
        session = async_get_clientsession(self.hass)
        try:
            async with async_timeout.timeout(15):
                response = await session.get(
                    f"http://{self._ip_address}/status.xml"
                )
                response.raise_for_status()
                body = await response.text()
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout while requesting status.xml") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error requesting status.xml: {err}") from err

        try:
            parsed: dict[str, str] = xmltodict.parse(body)["response"]
        except (KeyError, ValueError) as err:
            raise UpdateFailed("Invalid payload received from ventilation controller") from err

        return parsed
