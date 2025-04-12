"""Test the Picture Frame Controller config flow."""
from unittest.mock import patch, MagicMock

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.picture_frame_controller.const import (
    DOMAIN,
    CONF_MEDIA_PATHS,
    CONF_EXCLUDE_PATTERN,
    CONF_UPDATE_INTERVAL,
    CONF_IMAGE_EXTENSIONS,
    CONF_VIDEO_EXTENSIONS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_IMAGE_EXTENSIONS,
    DEFAULT_VIDEO_EXTENSIONS,
)


async def test_form(hass, mock_os_path_exists):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None

    # Test form validation
    mock_os_path_exists.return_value = True
    
    with patch(
        "custom_components.picture_frame_controller.config_flow.os.path.isdir",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_MEDIA_PATHS: ["/test/path/**"],
                CONF_UPDATE_INTERVAL: 60,
                CONF_IMAGE_EXTENSIONS: [".jpg", ".png"],
                CONF_VIDEO_EXTENSIONS: [".mp4"],
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Picture Frame Controller"
    assert result2["data"] == {
        CONF_MEDIA_PATHS: ["/test/path/**"],
        CONF_UPDATE_INTERVAL: 60,
        CONF_IMAGE_EXTENSIONS: [".jpg", ".png"],
        CONF_VIDEO_EXTENSIONS: [".mp4"],
    }


async def test_form_invalid_path(hass):
    """Test we handle invalid path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Test form validation with invalid path
    with patch(
        "custom_components.picture_frame_controller.config_flow.os.path.isdir",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_MEDIA_PATHS: ["/nonexistent/path/**"],
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {CONF_MEDIA_PATHS: "invalid_path"}


async def test_form_invalid_regex(hass, mock_os_path_exists):
    """Test we handle invalid regex patterns."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    mock_os_path_exists.return_value = True
    
    # Test form validation with invalid regex
    with patch(
        "custom_components.picture_frame_controller.config_flow.os.path.isdir",
        return_value=True,
    ), patch(
        "custom_components.picture_frame_controller.config_flow.re.compile",
        side_effect=Exception("Invalid regex"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_MEDIA_PATHS: ["/test/path/**"],
                CONF_EXCLUDE_PATTERN: ["[invalid regex"],
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {CONF_EXCLUDE_PATTERN: "invalid_regex"}


async def test_import_flow(hass, mock_os_path_exists):
    """Test the import flow."""
    mock_os_path_exists.return_value = True
    
    with patch(
        "custom_components.picture_frame_controller.config_flow.os.path.isdir",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data={
                CONF_MEDIA_PATHS: ["/imported/path/**"],
                CONF_UPDATE_INTERVAL: 45,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Picture Frame Controller"
    assert result["data"][CONF_MEDIA_PATHS] == ["/imported/path/**"]
    assert result["data"][CONF_UPDATE_INTERVAL] == 45