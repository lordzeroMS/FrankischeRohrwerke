import requests
import xmltodict
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    async_add_entities([
        LueftungsanlageSensor(ip_address, "aktuell0", "Lüftungsanlage Stufe", entry.entry_id),
        LueftungsanlageSensor(ip_address, "abl0", "Lüftungsanlage Abluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "zul0", "Lüftungsanlage Zuluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "aul0", "Lüftungsanlage Außenluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "fol0", "Lüftungsanlage Fortluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "rest_time", "Lüftungsanlage Filter Restzeit", entry.entry_id),
        LueftungsanlageSensor(ip_address, "bypass", "Lüftungsanlage Bypass Status", entry.entry_id)
    ])

class LueftungsanlageSensor(SensorEntity):
    def __init__(self, ip_address, sensor_type, name, entry_id):
        self._ip_address = ip_address
        self._sensor_type = sensor_type
        self._name = name
        self._entry_id = entry_id
        self._state = None
        self._attr_device_class = SensorDeviceClass.TEMPERATURE if "Temperatur" in name else None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self._entry_id}_{self._sensor_type}"

    def update(self):
        res_xml = requests.get(f"http://{self._ip_address}/status.xml")
        if res_xml.status_code == 200:
            res_xml = xmltodict.parse(res_xml.text)
            self._state = res_xml['response'].get(self._sensor_type)