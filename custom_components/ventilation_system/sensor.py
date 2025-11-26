from __future__ import annotations

from dataclasses import dataclass
import re
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


@dataclass
class VentilationSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, str]], Any] | None = None

    def value_from(self, data: dict[str, str]) -> Any:
        if self.value_fn:
            return self.value_fn(data)
        return data.get(self.key)


_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _value_as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        for item in value:
            text = _value_as_text(item)
            if text is not None:
                return text
        return None
    if isinstance(value, dict):
        # xmltodict wraps element content in "#text" when attributes exist
        text = value.get("#text") or value.get("text")
        if text is None:
            # try nested values (e.g. {"value": {"#text": "12"}})
            for nested_value in value.values():
                text = _value_as_text(nested_value)
                if text is not None:
                    return text
            return None
        return str(text)
    return str(value)


def _extract_number(value: Any) -> str | None:
    text = _value_as_text(value)
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    return match.group(0)


def _as_float(value: Any) -> float | None:
    numeric = _extract_number(value)
    if numeric is None:
        return None
    try:
        return float(numeric.replace(",", "."))
    except ValueError:
        return None


def _as_int(value: Any) -> int | None:
    numeric = _extract_number(value)
    if numeric is None:
        return None
    try:
        return int(float(numeric.replace(",", ".")))
    except ValueError:
        return None


def _stage_value(data: dict[str, str]) -> int | None:
    raw_value = _value_as_text(data.get("aktuell0"))
    if not raw_value:
        return None
    lower = raw_value.lower()
    if "stufe" in lower:
        try:
            return int(lower.split("stufe")[1].split()[0])
        except (IndexError, ValueError):
            return None
    return _as_int(raw_value)


SENSORS: tuple[VentilationSensorEntityDescription, ...] = (
    VentilationSensorEntityDescription(
        key="aktuell0",
        name="Ventilation Stage",
        icon="mdi:fan-speed-1",
        value_fn=_stage_value,
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
        value_fn=_as_int,
    ),
    VentilationSensorEntityDescription(
        key="filtertime",
        name="Filter Interval",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_int,
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
        value_fn=_as_float,
    ),
    VentilationSensorEntityDescription(
        key="zul0",
        name="Supply Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    VentilationSensorEntityDescription(
        key="aul0",
        name="Outdoor Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    VentilationSensorEntityDescription(
        key="fol0",
        name="Exhausted Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    VentilationSensorEntityDescription(
        key="BsSt1",
        name="Runtime Stage 1",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_as_int,
    ),
    VentilationSensorEntityDescription(
        key="BsSt2",
        name="Runtime Stage 2",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_as_int,
    ),
    VentilationSensorEntityDescription(
        key="BsSt3",
        name="Runtime Stage 3",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_as_int,
    ),
    VentilationSensorEntityDescription(
        key="BsSt4",
        name="Runtime Stage 4",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_as_int,
    ),
    VentilationSensorEntityDescription(
        key="partytime",
        name="Party Mode Duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        value_fn=_as_int,
    ),
    VentilationSensorEntityDescription(
        key="BipaAutAUL",
        name="Bypass Outdoor Threshold",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=_as_float,
    ),
    VentilationSensorEntityDescription(
        key="BipaAutABL",
        name="Bypass Exhaust Threshold",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=_as_float,
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
