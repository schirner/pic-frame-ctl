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
    ATTR_ENTITY_PICTURE,
    ATTR_IMAGE_NAME,
    ATTR_LAST_SHOWN,
    ATTR_MEDIA_PATH,
    ATTR_MONTH,
    ATTR_YEAR,
    CONF_DISPLAY_URI_PREFIX,
    CONF_FILE_SYSTEM_PREFIX,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DISPLAY_URI_PREFIX,
    DEFAULT_FILE_SYSTEM_PREFIX,
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
        
        # Get prefix configurations
        self._file_system_prefix = config_entry.data.get(
            CONF_FILE_SYSTEM_PREFIX, DEFAULT_FILE_SYSTEM_PREFIX
        )
        self._display_uri_prefix = config_entry.data.get(
            CONF_DISPLAY_URI_PREFIX, DEFAULT_DISPLAY_URI_PREFIX
        )

    def _replace_prefix(self, path: str) -> str:
        """Replace file system prefix with display URI prefix."""
        if path and path.startswith(self._file_system_prefix):
            return path.replace(self._file_system_prefix, self._display_uri_prefix, 1)
        return path

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
    def entity_picture(self) -> Optional[str]:
        """Return entity picture for the selected image."""
        if self.entity_description.key != SENSOR_SELECTED_IMAGE:
            return None
            
        if not self.coordinator.data:
            return None
            
        media_info = self.coordinator.data.get("selected_media")
        if not media_info:
            return None
            
        full_path = os.path.join(
            media_info.get("album_path", ""), 
            media_info.get("filename", "")
        )
        
        # Convert filesystem path to display URI
        return self._replace_prefix(full_path)

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

        file_path = os.path.join(
            media_info.get("album_path", ""), media_info.get("filename", "")
        )
        
        # Get the URI path for display
        display_path = self._replace_prefix(file_path)

        return {
            ATTR_ALBUM_NAME: media_info.get("album_name"),
            ATTR_YEAR: media_info.get("year"),
            ATTR_MONTH: media_info.get("month"),
            ATTR_MEDIA_PATH: file_path,
            ATTR_IMAGE_NAME: media_info.get("filename"),
            ATTR_LAST_SHOWN: media_info.get("last_shown"),
            ATTR_ENTITY_PICTURE: display_path,
        }
