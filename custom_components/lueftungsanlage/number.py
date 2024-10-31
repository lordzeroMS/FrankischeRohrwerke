import requests
from homeassistant.components.number import NumberEntity
from homeassistant.const import DEVICE_CLASS_POWER
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
        self._attr_device_class = DEVICE_CLASS_POWER

    @property
    def name(self):
        return "Lüftungsanlage Regler"

    @property
    def unique_id(self):
        return f"{self._entry_id}_regler"

    async def async_set_value(self, value):
        if 1 <= value <= 4:
            await self._hass.async_add_executor_job(
                requests.get, f"http://{self._ip_address}/stufe.cgi?stufe={value}"
            )
            self._attr_native_value = value