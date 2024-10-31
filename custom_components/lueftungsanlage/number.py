import aiohttp
import async_timeout
import xmltodict
import requests
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    async_add_entities([LueftungsanlageRegler(hass, ip_address, entry.entry_id)])

class LueftungsanlageRegler(NumberEntity):
    def __init__(self, hass, ip_address, entry_id):
        self._hass = hass
        self._ip_address = ip_address
        self._entry_id = entry_id
        self._attr_native_value = 1  # Default stage
        self._attr_native_min_value = 1
        self._attr_native_max_value = 4
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.POWER

    @property
    def name(self):
        return "Lüftungsanlage Regler"

    @property
    def unique_id(self):
        return f"{self._entry_id}_regler"

    async def async_set_native_value(self, value):
        if 1 <= value <= 4:
            response = await self._hass.async_add_executor_job(
                requests.get, f"http://{self._ip_address}/stufe.cgi?stufe={value}"
            )
            if response.status_code == 200:
                self._attr_native_value = value
                self.async_write_ha_state()

    async def fetch_current_value(self):
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self._ip_address}/status.xml") as response:
                    if response.status == 200:
                        text = await response.text()
                        data = xmltodict.parse(text)['response']
                        raw_value = data.get("aktuell0")
                        if raw_value and "Stufe" in raw_value:
                            self._attr_native_value = int(raw_value.split("Stufe")[1].split()[0])
                            self.async_write_ha_state()

    async def async_update(self):
        await self.fetch_current_value()