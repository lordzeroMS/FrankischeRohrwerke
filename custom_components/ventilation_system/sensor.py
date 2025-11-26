from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_IP_ADDRESS, DATA_COORDINATOR, DOMAIN
from .coordinator import VentilationDataCoordinator
from .parser import as_float, as_int, stage_value, value_as_text


@dataclass
class VentilationSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, str]], Any] | None = None
    value_transform: Callable[[Any], Any] | None = None

    def value_from(self, data: dict[str, str]) -> Any:
        if self.value_fn:
            return self.value_fn(data)
        value = data.get(self.key)
        if self.value_transform:
            return self.value_transform(value)
        return value_as_text(value)


SENSORS: tuple[VentilationSensorEntityDescription, ...] = (
    VentilationSensorEntityDescription(
        key="aktuell0",
        name="Ventilation Stage",
        icon="mdi:fan-speed-1",
        value_transform=stage_value,
    ),
    VentilationSensorEntityDescription(
        key="control0",
        name="Control Mode",
        icon="mdi:hand-back-left",
    ),
    VentilationSensorEntityDescription(
        key="bypass",
        name="Bypass Status",
        icon="mdi:cached",
    ),
    VentilationSensorEntityDescription(
        key="rest_time",
        name="Filter Remaining Time",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="filtertime",
        name="Filter Interval",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="filter0",
        name="Filter Status Text",
        icon="mdi:air-filter",
    ),
    VentilationSensorEntityDescription(
        key="events",
        name="Controller Events",
        icon="mdi:alert",
    ),
    VentilationSensorEntityDescription(
        key="abl0",
        name="Exhaust Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_transform=as_float,
    ),
    VentilationSensorEntityDescription(
        key="zul0",
        name="Supply Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_transform=as_float,
    ),
    VentilationSensorEntityDescription(
        key="aul0",
        name="Outdoor Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_transform=as_float,
    ),
    VentilationSensorEntityDescription(
        key="fol0",
        name="Exhausted Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_transform=as_float,
    ),
    VentilationSensorEntityDescription(
        key="BsSt1",
        name="Runtime Stage 1",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="BsSt2",
        name="Runtime Stage 2",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="BsSt3",
        name="Runtime Stage 3",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="BsSt4",
        name="Runtime Stage 4",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="partytime",
        name="Party Mode Duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        value_transform=as_int,
    ),
    VentilationSensorEntityDescription(
        key="BipaAutAUL",
        name="Bypass Outdoor Threshold",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_transform=as_float,
    ),
    VentilationSensorEntityDescription(
        key="BipaAutABL",
        name="Bypass Exhaust Threshold",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_transform=as_float,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: VentilationDataCoordinator = entry_data[DATA_COORDINATOR]

    async_add_entities(
        VentilationSystemSensor(
            coordinator, entry.entry_id, entry.data[CONF_IP_ADDRESS], description
        )
        for description in SENSORS
    )


class VentilationSystemSensor(CoordinatorEntity[VentilationDataCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VentilationDataCoordinator,
        entry_id: str,
        ip_address: str,
        description: VentilationSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Fraenkische Ventilation",
            manufacturer="Fraenkische Rohrwerke",
            model="profi-air",
            configuration_url=f"http://{ip_address}/",
        )

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_from(self.coordinator.data)
