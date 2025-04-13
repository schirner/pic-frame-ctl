"""The Picture Frame Controller integration."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import timedelta
from typing import Any, Dict, List, Optional
import pathlib

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
# Commenting out frontend imports for now
# from homeassistant.components.frontend import async_register_built_in_panel, add_extra_js_url
# from homeassistant.components.http.view import HomeAssistantView

from .const import (
    ATTR_ALBUM_NAME,
    ATTR_TIME_RANGE_END_MONTH,
    ATTR_TIME_RANGE_END_YEAR,
    ATTR_TIME_RANGE_START_MONTH,
    ATTR_TIME_RANGE_START_YEAR,
    CONF_EXCLUDE_PATTERN,
    CONF_IMAGE_EXTENSIONS,
    CONF_MEDIA_PATHS,
    CONF_UPDATE_INTERVAL,
    CONF_VIDEO_EXTENSIONS,
    DEFAULT_IMAGE_EXTENSIONS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VIDEO_EXTENSIONS,
    DOMAIN,
    SERVICE_CLEAR_ALBUM_FILTER,
    SERVICE_CLEAR_TIME_RANGE,
    SERVICE_NEXT_IMAGE,
    SERVICE_PREVIOUS_IMAGE,
    SERVICE_RESET_SEEN_STATUS,
    SERVICE_SCAN_MEDIA,
    SERVICE_SET_ALBUM_FILTER,
    SERVICE_SET_TIME_RANGE,
)
from .database_manager import DatabaseManager
from .media_scanner import MediaScanner

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_MEDIA_PATHS): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_EXCLUDE_PATTERN, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): cv.positive_int,
                vol.Optional(
                    CONF_IMAGE_EXTENSIONS, default=DEFAULT_IMAGE_EXTENSIONS
                ): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(
                    CONF_VIDEO_EXTENSIONS, default=DEFAULT_VIDEO_EXTENSIONS
                ): vol.All(cv.ensure_list, [cv.string]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Picture Frame Controller integration from YAML."""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    domain_config = config[DOMAIN]

    # Create a config entry from YAML configuration
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=domain_config,
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Picture Frame Controller from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Extract configuration
    config = entry.data
    media_paths = config.get(CONF_MEDIA_PATHS, [])
    exclude_patterns = config.get(CONF_EXCLUDE_PATTERN, [])
    update_interval = config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    image_extensions = config.get(CONF_IMAGE_EXTENSIONS, DEFAULT_IMAGE_EXTENSIONS)
    video_extensions = config.get(CONF_VIDEO_EXTENSIONS, DEFAULT_VIDEO_EXTENSIONS)
    
    # Create database manager
    db_manager = DatabaseManager(hass)
    
    # Create media scanner
    media_scanner = MediaScanner(
        hass,
        db_manager,
        media_paths,
        exclude_patterns,
        image_extensions,
        video_extensions,
    )
    
    # Create coordinator
    coordinator = PictureFrameCoordinator(
        hass,
        db_manager,
        update_interval
    )
    
    # Store objects in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "db_manager": db_manager,
        "media_scanner": media_scanner,
        "coordinator": coordinator,
        "config": config,
    }
    
    # Disabling frontend resources registration for now
    # await register_frontend_resources(hass)
    
    # Register services
    register_services(hass, entry)
    
    # Run initial scan if database is not yet created
    # This is done in a background task to avoid blocking setup
    hass.async_create_task(async_initial_scan(hass, entry))
    
    # Start the update coordinator
    await coordinator.async_config_entry_first_refresh()
    
    # Make sure to close database connection on shutdown
    async def close_db_on_shutdown(_):
        db_manager.close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_db_on_shutdown)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


# Commenting out the frontend resources registration function for now
"""
async def register_frontend_resources(hass: HomeAssistant) -> None:
    # Get the URL for the frontend resources
    root_path = pathlib.Path(__file__).parent
    frontend_path = root_path / "frontend"
    
    # Register the card module
    module_url = f"/picture_frame_controller-{DOMAIN}.js"
    
    # Create and register a view that serves the resource
    class PictureFrameCardJsView(HomeAssistantView):
        requires_auth = False
        url = module_url
        name = f"picture_frame_controller_js"
        
        async def get(self, request):
            # Handle GET request for the card JS file.
            js_file = frontend_path / "picture-frame-card.js"
            if not js_file.exists():
                _LOGGER.error(f"Frontend resource not found: {js_file}")
                return None
                
            with open(js_file, "r") as file:
                content = file.read()
            
            return content
    
    hass.http.register_view(PictureFrameCardJsView())
    
    # Register the resource with Home Assistant
    add_extra_js_url(hass, module_url)
    
    _LOGGER.info(f"Registered picture-frame-card Lovelace card: {module_url}")
"""


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass_data = hass.data[DOMAIN]
        entry_data = hass_data.pop(entry.entry_id)
        
        # Close database connection
        db_manager = entry_data.get("db_manager")
        if db_manager:
            db_manager.close()
    
    return unload_ok


class PictureFrameCoordinator(DataUpdateCoordinator):
    """Class to coordinate picture frame updates."""

    def __init__(self, hass: HomeAssistant, db_manager: DatabaseManager, update_interval: int):
        """Initialize the coordinator."""
        self.db_manager = db_manager
        self._current_media_id = None
        self._album_filter = None
        self._time_range = {
            "start_year": None,
            "start_month": None,
            "end_year": None,
            "end_month": None,
        }

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data for the coordinator."""
        try:
            # Count all media files
            count_total = await self.hass.async_add_executor_job(
                self.db_manager.get_media_count
            )
            
            # Count unseen media files
            count_unseen = await self.hass.async_add_executor_job(
                self.db_manager.get_unseen_count, self._album_filter
            )
            
            # Get random unseen media
            selected_media = await self.hass.async_add_executor_job(
                self._get_next_media
            )
            
            # Mark the selected media as seen if it's new
            if selected_media and selected_media.get("id") != self._current_media_id:
                self._current_media_id = selected_media["id"]
                await self.hass.async_add_executor_job(
                    self.db_manager.mark_media_as_seen, selected_media["id"]
                )
            
            return {
                "selected_media": selected_media,
                "count_total": count_total,
                "count_unseen": count_unseen,
            }
        except Exception as err:
            _LOGGER.error("Error updating coordinator data: %s", err)
            raise UpdateFailed(f"Error updating data: {err}") from err

    def _get_next_media(self) -> Optional[Dict[str, Any]]:
        """Get the next media to display."""
        # Try to get a random unseen media
        media = self.db_manager.get_random_unseen_media(
            album_id=self._album_filter,
            start_year=self._time_range.get("start_year"),
            start_month=self._time_range.get("start_month"),
            end_year=self._time_range.get("end_year"),
            end_month=self._time_range.get("end_month"),
        )
        
        # If no unseen media found, reset and try again
        if not media:
            # If album filter is set, reset just for this album
            if self._album_filter is not None:
                self.db_manager.reset_seen_status(album_id=self._album_filter)
                media = self.db_manager.get_random_unseen_media(album_id=self._album_filter)
            # If time range filter is set, reset for time range
            elif all(self._time_range.values()):
                self.db_manager.reset_seen_status(
                    time_range=True,
                    start_year=self._time_range.get("start_year"),
                    start_month=self._time_range.get("start_month"),
                    end_year=self._time_range.get("end_year"),
                    end_month=self._time_range.get("end_month"),
                )
                media = self.db_manager.get_random_unseen_media(
                    start_year=self._time_range.get("start_year"),
                    start_month=self._time_range.get("start_month"),
                    end_year=self._time_range.get("end_year"),
                    end_month=self._time_range.get("end_month"),
                )
            # Otherwise reset all
            else:
                self.db_manager.reset_seen_status()
                media = self.db_manager.get_random_unseen_media()
        
        return media

    def set_album_filter(self, album_id: Optional[int]) -> None:
        """Set the album filter."""
        self._album_filter = album_id
        
        # If the album filter is set to an album with 0 unseen images, 
        # reset seen status for this album
        if album_id is not None:
            unseen_count = self.db_manager.get_unseen_count(album_id=album_id)
            if unseen_count == 0:
                self.db_manager.reset_seen_status(album_id=album_id)

    def clear_album_filter(self) -> None:
        """Clear the album filter."""
        self._album_filter = None

    def set_time_range(
        self, start_year: int, start_month: int, end_year: int, end_month: int
    ) -> None:
        """Set the time range filter."""
        self._time_range = {
            "start_year": start_year,
            "start_month": start_month,
            "end_year": end_year,
            "end_month": end_month,
        }

    def clear_time_range(self) -> None:
        """Clear the time range filter."""
        self._time_range = {
            "start_year": None,
            "start_month": None,
            "end_year": None,
            "end_month": None,
        }

    async def show_next_image(self) -> None:
        """Show the next image immediately."""
        await self.async_refresh()

    async def show_previous_image(self) -> None:
        """Show the previous image."""
        if not self._current_media_id:
            return
            
        # Get previously shown media
        previous_media = await self.hass.async_add_executor_job(
            self.db_manager.get_previously_shown_media,
            self._current_media_id,
            self._album_filter,
            self._time_range.get("start_year"),
            self._time_range.get("start_month"),
            self._time_range.get("end_year"),
            self._time_range.get("end_month"),
        )
        
        if previous_media:
            self._current_media_id = previous_media["id"]
            self.data = {
                "selected_media": previous_media,
                "count_total": self.data.get("count_total", 0),
                "count_unseen": self.data.get("count_unseen", 0),
            }
            self.async_update_listeners()


async def async_initial_scan(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Run an initial scan if database does not exist."""
    _LOGGER.info("Running initial media scan")
    
    entry_data = hass.data[DOMAIN][entry.entry_id]
    media_scanner = entry_data["media_scanner"]
    
    # Run the scan in an executor to avoid blocking
    await hass.async_add_executor_job(media_scanner.scan)
    
    # Update the coordinator after scan
    coordinator = entry_data["coordinator"]
    await coordinator.async_refresh()
    
    _LOGGER.info("Initial media scan completed")


def register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register services for the integration."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    db_manager = entry_data["db_manager"]
    media_scanner = entry_data["media_scanner"]

    async def handle_next_image(call: ServiceCall) -> None:
        """Handle next_image service call."""
        await coordinator.show_next_image()

    async def handle_previous_image(call: ServiceCall) -> None:
        """Handle previous_image service call."""
        await coordinator.show_previous_image()

    async def handle_set_album_filter(call: ServiceCall) -> None:
        """Handle set_album_filter service call."""
        album_name = call.data.get(ATTR_ALBUM_NAME)
        
        # Find the album ID by name
        albums = await hass.async_add_executor_job(db_manager.get_albums)
        album_id = None
        
        for album in albums:
            if album["name"] == album_name:
                album_id = album["id"]
                break
                
        if album_id is not None:
            coordinator.set_album_filter(album_id)
            await coordinator.async_refresh()
        else:
            _LOGGER.warning("Album not found: %s", album_name)

    async def handle_clear_album_filter(call: ServiceCall) -> None:
        """Handle clear_album_filter service call."""
        coordinator.clear_album_filter()
        await coordinator.async_refresh()

    async def handle_set_time_range(call: ServiceCall) -> None:
        """Handle set_time_range service call."""
        start_year = call.data.get(ATTR_TIME_RANGE_START_YEAR)
        start_month = call.data.get(ATTR_TIME_RANGE_START_MONTH)
        end_year = call.data.get(ATTR_TIME_RANGE_END_YEAR)
        end_month = call.data.get(ATTR_TIME_RANGE_END_MONTH)
        
        if all([start_year, start_month, end_year, end_month]):
            coordinator.set_time_range(start_year, start_month, end_year, end_month)
            await coordinator.async_refresh()

    async def handle_clear_time_range(call: ServiceCall) -> None:
        """Handle clear_time_range service call."""
        coordinator.clear_time_range()
        await coordinator.async_refresh()

    async def handle_reset_seen_status(call: ServiceCall) -> None:
        """Handle reset_seen_status service call."""
        await hass.async_add_executor_job(db_manager.reset_seen_status)
        await coordinator.async_refresh()

    async def handle_scan_media(call: ServiceCall) -> None:
        """Handle scan_media service call."""
        await async_initial_scan(hass, entry)

    # Register services
    hass.services.async_register(DOMAIN, SERVICE_NEXT_IMAGE, handle_next_image)
    hass.services.async_register(DOMAIN, SERVICE_PREVIOUS_IMAGE, handle_previous_image)
    hass.services.async_register(DOMAIN, SERVICE_SET_ALBUM_FILTER, handle_set_album_filter)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_ALBUM_FILTER, handle_clear_album_filter)
    hass.services.async_register(DOMAIN, SERVICE_SET_TIME_RANGE, handle_set_time_range)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_TIME_RANGE, handle_clear_time_range)
    hass.services.async_register(DOMAIN, SERVICE_RESET_SEEN_STATUS, handle_reset_seen_status)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_MEDIA, handle_scan_media)