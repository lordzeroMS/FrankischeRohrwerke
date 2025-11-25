from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_IP_ADDRESS, DATA_COORDINATOR, DOMAIN
from .coordinator import VentilationDataCoordinator


@dataclass
class VentilationBinarySensorDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[dict[str, str]], bool] | None = None

    def is_on(self, data: dict[str, str]) -> bool | None:
        if not self.is_on_fn:
            return None
        return self.is_on_fn(data)


def _bool_from_text(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.strip().lower() == "ein"


BINARY_SENSORS: tuple[VentilationBinarySensorDescription, ...] = (
    VentilationBinarySensorDescription(
        key="filter0",
        name="Filter Replacement Needed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda data: "filterwechsel" in (data.get("filter0") or "").lower(),
    ),
    VentilationBinarySensorDescription(
        key="DiIn1",
        name="Digital Input 1",
        is_on_fn=lambda data: _bool_from_text(data.get("DiIn1")),
    ),
    VentilationBinarySensorDescription(
        key="DiIn2",
        name="Digital Input 2",
        is_on_fn=lambda data: _bool_from_text(data.get("DiIn2")),
    ),
    VentilationBinarySensorDescription(
        key="DiIn3",
        name="Digital Input 3",
        is_on_fn=lambda data: _bool_from_text(data.get("DiIn3")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: VentilationDataCoordinator = entry_data[DATA_COORDINATOR]

    async_add_entities(
        VentilationBinarySensor(
            coordinator, entry.entry_id, entry.data[CONF_IP_ADDRESS], description
        )
        for description in BINARY_SENSORS
    )


class VentilationBinarySensor(
    CoordinatorEntity[VentilationDataCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VentilationDataCoordinator,
        entry_id: str,
        ip_address: str,
        description: VentilationBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_{description.key}_binary"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Fraenkische Ventilation",
            manufacturer="Fraenkische Rohrwerke",
            model="profi-air",
            configuration_url=f"http://{ip_address}/",
        )

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.entity_description.is_on(self.coordinator.data)
