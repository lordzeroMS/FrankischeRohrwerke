import requests
import xmltodict
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    async_add_entities([LueftungsanlageSensor(ip_address)])

class LueftungsanlageSensor(SensorEntity):
    def __init__(self, ip_address):
        self._ip_address = ip_address
        self._state = None

    @property
    def name(self):
        return "Lüftungsanlage Sensor"

    @property
    def state(self):
        return self._state

    def update(self):
        res_xml = requests.get(f"http://{self._ip_address}/status.xml")
        if res_xml.status_code == 200:
            res_xml = xmltodict.parse(res_xml.text)
            self._state = res_xml['response'].get('aktuell0')