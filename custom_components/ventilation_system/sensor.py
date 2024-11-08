import aiohttp
import async_timeout
import requests
import xmltodict
import time
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from .const import DOMAIN, CONF_IP_ADDRESS

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data[CONF_IP_ADDRESS]
    sensors = [
        VentilationSystemSensor(hass, ip_address, "aktuell0", "Lüftungsanlage Stufe", entry.entry_id),
        VentilationSystemSensor(hass, ip_address, "abl0", "Lüftungsanlage Abluft Temperatur", entry.entry_id),
        VentilationSystemSensor(hass, ip_address, "zul0", "Lüftungsanlage Zuluft Temperatur", entry.entry_id),
        VentilationSystemSensor(hass, ip_address, "aul0", "Lüftungsanlage Außenluft Temperatur", entry.entry_id),
        VentilationSystemSensor(hass, ip_address, "fol0", "Lüftungsanlage Fortluft Temperatur", entry.entry_id),
        VentilationSystemSensor(hass, ip_address, "rest_time", "Lüftungsanlage Filter Restzeit", entry.entry_id),
        VentilationSystemSensor(hass, ip_address, "bypass", "Lüftungsanlage Bypass Status", entry.entry_id)
    ]
    async_add_entities(sensors)
    await VentilationSystemSensor.update_all_sensors(sensors)


class VentilationSystemSensor(SensorEntity):
    _shared_data = None
    _last_update = 0

    def __init__(self, hass, ip_address, sensor_type, name, entry_id):
        self._hass = hass
        self._ip_address = ip_address
        self._sensor_type = sensor_type
        self._name = name
        self._entry_id = entry_id
        self._state = None
        self._attr_device_class = SensorDeviceClass.TEMPERATURE if "Temperatur" in name else None
        self._attr_unit_of_measurement = "°C" if "Temperatur" in name else None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self._entry_id}_{self._sensor_type}"

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

    @classmethod
    async def update_all_sensors(cls, sensors):
        current_time = time.time()
        if cls._shared_data is None or (current_time - cls._last_update) > 5:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{sensors[0]._ip_address}/status.xml") as response:
                        if response.status == 200:
                            text = await response.text()
                            cls._shared_data = xmltodict.parse(text)['response']
                            cls._last_update = current_time
        for sensor in sensors:
            sensor.update_from_shared_data()

    def update_from_shared_data(self):
        raw_value = self._shared_data.get(self._sensor_type)
        if self._sensor_type == "aktuell0" and raw_value and "Stufe" in raw_value:
            self._state = int(raw_value.split("Stufe")[1].split()[0])
        else:
            self._state = raw_value

    async def async_update(self):
        await self.update_all_sensors([self])

class LueftungsanlageRegler(NumberEntity):
    def __init__(self, hass, ip_address, entry_id, sensor):
        self._hass = hass
        self._ip_address = ip_address
        self._entry_id = entry_id
        self._sensor = sensor
        self._attr_native_value = 1  # Default stage
        self._attr_native_min_value = 1
        self._attr_native_max_value = 4
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.POWER

    @property
    def name(self):
        return "Ventilation System Sensor"

    @property
    def unique_id(self):
        return f"{self._entry_id}_regler_2"

    async def async_set_native_value(self, value):
        if 1 <= value <= 4:
            await self._hass.async_add_executor_job(
                requests.get, f"http://{self._ip_address}/stufe.cgi?stufe={value}"
            )
            self._attr_native_value = value
            self.async_write_ha_state()

    async def async_update(self):
        self._attr_native_value = self._sensor.state
        self.async_write_ha_state()