import requests
import xmltodict
import time
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    sensors = [
        LueftungsanlageSensor(ip_address, "aktuell0", "Lüftungsanlage Stufe", entry.entry_id),
        LueftungsanlageSensor(ip_address, "abl0", "Lüftungsanlage Abluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "zul0", "Lüftungsanlage Zuluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "aul0", "Lüftungsanlage Außenluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "fol0", "Lüftungsanlage Fortluft Temperatur", entry.entry_id),
        LueftungsanlageSensor(ip_address, "rest_time", "Lüftungsanlage Filter Restzeit", entry.entry_id),
        LueftungsanlageSensor(ip_address, "bypass", "Lüftungsanlage Bypass Status", entry.entry_id)
    ]
    async_add_entities(sensors)
    LueftungsanlageSensor.update_all_sensors(sensors)

class LueftungsanlageSensor(SensorEntity):
    _shared_data = None
    _last_update = 0

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

    @classmethod
    def update_all_sensors(cls, sensors):
        current_time = time.time()
        if cls._shared_data is None or (current_time - cls._last_update) > 5:
            res_xml = requests.get(f"http://{sensors[0]._ip_address}/status.xml")
            if res_xml.status_code == 200:
                cls._shared_data = xmltodict.parse(res_xml.text)['response']
                cls._last_update = current_time
        for sensor in sensors:
            sensor.update_from_shared_data()

    def update_from_shared_data(self):
        raw_value = self._shared_data.get(self._sensor_type)
        if self._sensor_type == "aktuell0" and raw_value and "Stufe" in raw_value:
            self._state = int(raw_value.split("Stufe")[1].split()[0])
        else:
            self._state = raw_value

    def update(self):
        self.update_all_sensors([self])