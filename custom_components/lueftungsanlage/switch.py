import requests
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    async_add_entities([LueftungsanlageSwitch(ip_address)])

class LueftungsanlageSwitch(SwitchEntity):
    def __init__(self, ip_address):
        self._ip_address = ip_address
        self._is_on = False
        self._stufe = 1  # Default stage

    @property
    def name(self):
        return "Lüftungsanlage Switch"

    @property
    def is_on(self):
        return self._is_on

    def turn_on(self, **kwargs):
        self._stufe = kwargs.get('stufe', 1)  # Get the stage from kwargs, default to 1
        if 1 <= self._stufe <= 4:
            requests.get(f"http://{self._ip_address}/stufe.cgi?stufe={self._stufe}")
            self._is_on = True