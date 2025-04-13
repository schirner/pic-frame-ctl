"""Sensor platform for picture frame controller."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_ALBUM_NAME,
    ATTR_IMAGE_NAME,
    ATTR_LAST_SHOWN,
    ATTR_MEDIA_PATH,
    ATTR_MONTH,
    ATTR_YEAR,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SENSOR_COUNT_IMAGE,
    SENSOR_COUNT_UNSEEN,
    SENSOR_SELECTED_IMAGE,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key=SENSOR_SELECTED_IMAGE,
        name="Selected Image",
        icon="mdi:image",
    ),
    SensorEntityDescription(
        key=SENSOR_COUNT_IMAGE,
        name="Total Images",
        icon="mdi:counter",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key=SENSOR_COUNT_UNSEEN,
        name="Unseen Images",
        icon="mdi:eye-off",
        device_class=SensorDeviceClass.ENUM,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the picture frame controller sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []
    for description in SENSOR_DESCRIPTIONS:
        entities.append(PictureFrameSensor(coordinator, description, config_entry))

    async_add_entities(entities)


class PictureFrameSensor(CoordinatorEntity, SensorEntity):
    """Picture frame controller sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{entity_description.key}"
        self._attr_name = f"{entity_description.name}"
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        if self.entity_description.key == SENSOR_SELECTED_IMAGE:
            media_info = self.coordinator.data.get("selected_media")
            if media_info:
                return os.path.join(
                    media_info.get("album_path", ""), media_info.get("filename", "")
                )
            return None

        elif self.entity_description.key == SENSOR_COUNT_IMAGE:
            return self.coordinator.data.get("count_total", 0)

        elif self.entity_description.key == SENSOR_COUNT_UNSEEN:
            return self.coordinator.data.get("count_unseen", 0)

        return None

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return entity specific state attributes."""
        if self.entity_description.key != SENSOR_SELECTED_IMAGE:
            return None

        # Only the selected image sensor has additional attributes
        if not self.coordinator.data:
            return None

        media_info = self.coordinator.data.get("selected_media")
        if not media_info:
            return None

        return {
            ATTR_ALBUM_NAME: media_info.get("album_name"),
            ATTR_YEAR: media_info.get("year"),
            ATTR_MONTH: media_info.get("month"),
            ATTR_MEDIA_PATH: os.path.join(
                media_info.get("album_path", ""), media_info.get("filename", "")
            ),
            ATTR_IMAGE_NAME: media_info.get("filename"),
            ATTR_LAST_SHOWN: media_info.get("last_shown"),
        }
