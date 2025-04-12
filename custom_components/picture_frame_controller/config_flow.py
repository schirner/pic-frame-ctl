"""Config flow for Picture Frame Controller integration."""
import os
import re
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_EXCLUDE_PATTERN,
    CONF_IMAGE_EXTENSIONS,
    CONF_MEDIA_PATHS,
    CONF_UPDATE_INTERVAL,
    CONF_VIDEO_EXTENSIONS,
    DEFAULT_IMAGE_EXTENSIONS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VIDEO_EXTENSIONS,
    DOMAIN,
)


class PictureFrameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Picture Frame Controller."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate the media paths
                for path in user_input[CONF_MEDIA_PATHS]:
                    base_path = path
                    if path.endswith("/**") or path.endswith("/*"):
                        base_path = path[:-2] if path.endswith("/*") else path[:-3]
                        
                    if not os.path.isdir(base_path):
                        errors[CONF_MEDIA_PATHS] = "invalid_path"
                        break

                # Validate exclude patterns
                if CONF_EXCLUDE_PATTERN in user_input:
                    try:
                        for pattern in user_input[CONF_EXCLUDE_PATTERN]:
                            re.compile(pattern)
                    except re.error:
                        errors[CONF_EXCLUDE_PATTERN] = "invalid_regex"

                # If no errors, create the entry
                if not errors:
                    return self.async_create_entry(
                        title="Picture Frame Controller",
                        data=user_input,
                    )
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MEDIA_PATHS): cv.multi_select({
                        # This would normally be populated with actual directory options
                        # For now it's an empty dictionary as we'd use dynamic options in a real setup
                    }),
                    vol.Optional(CONF_EXCLUDE_PATTERN): cv.multi_select({}),
                    vol.Optional(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_IMAGE_EXTENSIONS, default=DEFAULT_IMAGE_EXTENSIONS
                    ): cv.multi_select({ext: ext for ext in DEFAULT_IMAGE_EXTENSIONS}),
                    vol.Optional(
                        CONF_VIDEO_EXTENSIONS, default=DEFAULT_VIDEO_EXTENSIONS
                    ): cv.multi_select({ext: ext for ext in DEFAULT_VIDEO_EXTENSIONS}),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PictureFrameOptionsFlow(config_entry)


class PictureFrameOptionsFlow(config_entries.OptionsFlow):
    """Picture frame controller options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MEDIA_PATHS, 
                        default=self.config_entry.data.get(CONF_MEDIA_PATHS, [])
                    ): cv.multi_select({}),
                    vol.Optional(
                        CONF_EXCLUDE_PATTERN, 
                        default=self.config_entry.data.get(CONF_EXCLUDE_PATTERN, [])
                    ): cv.multi_select({}),
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_IMAGE_EXTENSIONS,
                        default=self.config_entry.data.get(CONF_IMAGE_EXTENSIONS, DEFAULT_IMAGE_EXTENSIONS),
                    ): cv.multi_select({ext: ext for ext in DEFAULT_IMAGE_EXTENSIONS}),
                    vol.Optional(
                        CONF_VIDEO_EXTENSIONS,
                        default=self.config_entry.data.get(CONF_VIDEO_EXTENSIONS, DEFAULT_VIDEO_EXTENSIONS),
                    ): cv.multi_select({ext: ext for ext in DEFAULT_VIDEO_EXTENSIONS}),
                }
            ),
        )