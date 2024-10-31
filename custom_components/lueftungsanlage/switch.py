import requests
from homeassistant.components.number import NumberEntity
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    async_add_entities([LueftungsanlageRegler(ip_address)])

class LueftungsanlageRegler(NumberEntity):
    def __init__(self, ip_address):
        self._ip_address = ip_address
        self._value = 1  # Default stage

    @property
    def name(self):
        return "Lüftungsanlage Regler"

    @property
    def min_value(self):
        return 1

    @property
    def max_value(self):
        return 4

    @property
    def step(self):
        return 1

    @property
    def value(self):
        return self._value

    def set_value(self, value):
        if 1 <= value <= 4:
            requests.get(f"http://{self._ip_address}/stufe.cgi?stufe={value}")
            self._value = value