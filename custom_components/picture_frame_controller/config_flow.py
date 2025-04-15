"""Config flow for Picture Frame Controller integration."""

import os
import re
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_EXCLUDE_PATTERN,
    CONF_FILE_SYSTEM_PREFIX,
    CONF_DISPLAY_URI_PREFIX,
    CONF_IMAGE_EXTENSIONS,
    CONF_MEDIA_PATHS,
    CONF_UPDATE_INTERVAL,
    CONF_VIDEO_EXTENSIONS,
    DEFAULT_IMAGE_EXTENSIONS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VIDEO_EXTENSIONS,
    DEFAULT_FILE_SYSTEM_PREFIX,
    DEFAULT_DISPLAY_URI_PREFIX,
    DOMAIN,
)


class PictureFrameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Picture Frame Controller."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.media_paths: list[str] = []
        self.exclude_patterns: list[str] = []

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        # Create entry from import
        return self.async_create_entry(
            title="Picture Frame Controller",
            data=import_config,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Handle adding a new media path
            if "media_path_add" in user_input and user_input["media_path_add"]:
                new_path = user_input["media_path_add"]
                self.media_paths.append(new_path)
                # Return to the form to show the updated paths
                return await self.async_step_user()

            # Handle adding a new exclude pattern
            if (
                "exclude_pattern_add" in user_input
                and user_input["exclude_pattern_add"]
            ):
                new_pattern = user_input["exclude_pattern_add"]
                self.exclude_patterns.append(new_pattern)
                # Return to the form to show the updated patterns
                return await self.async_step_user()

            # Check if this is a final submission
            if CONF_MEDIA_PATHS in user_input:
                try:
                    # Process paths
                    selected_paths = user_input.get(CONF_MEDIA_PATHS, [])
                    if not selected_paths:
                        errors[CONF_MEDIA_PATHS] = "required"
                    else:
                        # Validate the media paths
                        for path in selected_paths:
                            base_path = path
                            if path.endswith("/**") or path.endswith("/*"):
                                base_path = (
                                    path[:-2] if path.endswith("/*") else path[:-3]
                                )

                            if not os.path.isdir(base_path):
                                errors[CONF_MEDIA_PATHS] = "invalid_path"
                                break

                    # Validate exclude patterns
                    selected_patterns = user_input.get(CONF_EXCLUDE_PATTERN, [])
                    if selected_patterns:
                        try:
                            for pattern in selected_patterns:
                                re.compile(pattern)
                        except re.error:
                            errors[CONF_EXCLUDE_PATTERN] = "invalid_regex"

                    # If no errors, create the entry
                    if not errors:
                        final_data = {
                            CONF_MEDIA_PATHS: selected_paths,
                            CONF_EXCLUDE_PATTERN: selected_patterns,
                            CONF_UPDATE_INTERVAL: user_input.get(
                                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                            ),
                            CONF_IMAGE_EXTENSIONS: user_input.get(
                                CONF_IMAGE_EXTENSIONS, DEFAULT_IMAGE_EXTENSIONS
                            ),
                            CONF_VIDEO_EXTENSIONS: user_input.get(
                                CONF_VIDEO_EXTENSIONS, DEFAULT_VIDEO_EXTENSIONS
                            ),
                            CONF_FILE_SYSTEM_PREFIX: user_input.get(
                                CONF_FILE_SYSTEM_PREFIX, DEFAULT_FILE_SYSTEM_PREFIX
                            ),
                            CONF_DISPLAY_URI_PREFIX: user_input.get(
                                CONF_DISPLAY_URI_PREFIX, DEFAULT_DISPLAY_URI_PREFIX
                            ),
                        }
                        return self.async_create_entry(
                            title="Picture Frame Controller",
                            data=final_data,
                        )
                except Exception:  # pylint: disable=broad-except
                    errors["base"] = "unknown"

        # Create schema with options reflecting current values
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MEDIA_PATHS, default=self.media_paths
                ): cv.multi_select({path: path for path in self.media_paths}),
                vol.Optional("media_path_add"): cv.string,
                vol.Optional(
                    CONF_EXCLUDE_PATTERN, default=self.exclude_patterns
                ): cv.multi_select(
                    {pattern: pattern for pattern in self.exclude_patterns}
                ),
                vol.Optional("exclude_pattern_add"): cv.string,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): cv.positive_int,
                vol.Optional(
                    CONF_IMAGE_EXTENSIONS,
                    default=DEFAULT_IMAGE_EXTENSIONS,
                ): cv.multi_select({ext: ext for ext in DEFAULT_IMAGE_EXTENSIONS}),
                vol.Optional(
                    CONF_VIDEO_EXTENSIONS,
                    default=DEFAULT_VIDEO_EXTENSIONS,
                ): cv.multi_select({ext: ext for ext in DEFAULT_VIDEO_EXTENSIONS}),
                vol.Optional(
                    CONF_FILE_SYSTEM_PREFIX,
                    default=DEFAULT_FILE_SYSTEM_PREFIX,
                ): cv.string,
                vol.Optional(
                    CONF_DISPLAY_URI_PREFIX,
                    default=DEFAULT_DISPLAY_URI_PREFIX,
                ): cv.string,
            }
        )

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            last_step=True,
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
        super().__init__()
        # Don't store config_entry as an instance attribute
        # It's already available as self.config_entry in the OptionsFlow base class
        self.media_paths = list(config_entry.data.get(CONF_MEDIA_PATHS, []))
        self.exclude_patterns = list(config_entry.data.get(CONF_EXCLUDE_PATTERN, []))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Process media paths
            if "media_path_add" in user_input and user_input["media_path_add"]:
                self.media_paths.append(user_input["media_path_add"])
                # Return to the form to show the updated paths
                return await self.async_step_init()

            # Process exclude patterns
            if (
                "exclude_pattern_add" in user_input
                and user_input["exclude_pattern_add"]
            ):
                self.exclude_patterns.append(user_input["exclude_pattern_add"])
                # Return to the form to show the updated patterns
                return await self.async_step_init()

            # If this is a final submission
            if CONF_MEDIA_PATHS in user_input:
                # Extract only the options needed, don't send the full data object
                options = {
                    CONF_MEDIA_PATHS: list(user_input.get(CONF_MEDIA_PATHS, [])),
                    CONF_EXCLUDE_PATTERN: list(
                        user_input.get(CONF_EXCLUDE_PATTERN, [])
                    ),
                    CONF_UPDATE_INTERVAL: user_input.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                    CONF_IMAGE_EXTENSIONS: list(
                        user_input.get(CONF_IMAGE_EXTENSIONS, DEFAULT_IMAGE_EXTENSIONS)
                    ),
                    CONF_VIDEO_EXTENSIONS: list(
                        user_input.get(CONF_VIDEO_EXTENSIONS, DEFAULT_VIDEO_EXTENSIONS)
                    ),
                    CONF_FILE_SYSTEM_PREFIX: user_input.get(
                        CONF_FILE_SYSTEM_PREFIX, DEFAULT_FILE_SYSTEM_PREFIX
                    ),
                    CONF_DISPLAY_URI_PREFIX: user_input.get(
                        CONF_DISPLAY_URI_PREFIX, DEFAULT_DISPLAY_URI_PREFIX
                    ),
                }

                return self.async_create_entry(title="", data=options)

        # Create the schema for the options form
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MEDIA_PATHS, default=self.media_paths
                ): cv.multi_select({path: path for path in self.media_paths}),
                vol.Optional("media_path_add"): cv.string,
                vol.Optional(
                    CONF_EXCLUDE_PATTERN, default=self.exclude_patterns
                ): cv.multi_select(
                    {pattern: pattern for pattern in self.exclude_patterns}
                ),
                vol.Optional("exclude_pattern_add"): cv.string,
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.data.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): cv.positive_int,
                vol.Optional(
                    CONF_IMAGE_EXTENSIONS,
                    default=self.config_entry.data.get(
                        CONF_IMAGE_EXTENSIONS, DEFAULT_IMAGE_EXTENSIONS
                    ),
                ): cv.multi_select({ext: ext for ext in DEFAULT_IMAGE_EXTENSIONS}),
                vol.Optional(
                    CONF_VIDEO_EXTENSIONS,
                    default=self.config_entry.data.get(
                        CONF_VIDEO_EXTENSIONS, DEFAULT_VIDEO_EXTENSIONS
                    ),
                ): cv.multi_select({ext: ext for ext in DEFAULT_VIDEO_EXTENSIONS}),
                vol.Optional(
                    CONF_FILE_SYSTEM_PREFIX,
                    default=self.config_entry.data.get(
                        CONF_FILE_SYSTEM_PREFIX, DEFAULT_FILE_SYSTEM_PREFIX
                    ),
                ): cv.string,
                vol.Optional(
                    CONF_DISPLAY_URI_PREFIX,
                    default=self.config_entry.data.get(
                        CONF_DISPLAY_URI_PREFIX, DEFAULT_DISPLAY_URI_PREFIX
                    ),
                ): cv.string,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
