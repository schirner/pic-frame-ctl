"""Test Picture Frame Controller setup."""
from unittest.mock import patch, MagicMock, call

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component

from custom_components.picture_frame_controller.const import (
    DOMAIN,
    CONF_MEDIA_PATHS,
    SENSOR_SELECTED_IMAGE,
    SENSOR_COUNT_IMAGE,
    SENSOR_COUNT_UNSEEN,
    SERVICE_NEXT_IMAGE,
    SERVICE_PREVIOUS_IMAGE,
    SERVICE_SET_ALBUM_FILTER,
    SERVICE_CLEAR_ALBUM_FILTER,
    SERVICE_SET_TIME_RANGE,
    SERVICE_CLEAR_TIME_RANGE,
    SERVICE_RESET_SEEN_STATUS,
    SERVICE_SCAN_MEDIA,
    ATTR_ALBUM_NAME,
    ATTR_TIME_RANGE_START_YEAR,
    ATTR_TIME_RANGE_START_MONTH,
    ATTR_TIME_RANGE_END_YEAR,
    ATTR_TIME_RANGE_END_MONTH,
)


async def test_setup_component(hass, mock_db_manager, mock_media_scanner):
    """Test component is set up correctly."""
    config = {
        DOMAIN: {
            CONF_MEDIA_PATHS: ["/test/path/**"],
        }
    }

    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()

    # Check that all services are registered
    assert hass.services.has_service(DOMAIN, SERVICE_NEXT_IMAGE)
    assert hass.services.has_service(DOMAIN, SERVICE_PREVIOUS_IMAGE)
    assert hass.services.has_service(DOMAIN, SERVICE_SET_ALBUM_FILTER)
    assert hass.services.has_service(DOMAIN, SERVICE_CLEAR_ALBUM_FILTER)
    assert hass.services.has_service(DOMAIN, SERVICE_SET_TIME_RANGE)
    assert hass.services.has_service(DOMAIN, SERVICE_CLEAR_TIME_RANGE)
    assert hass.services.has_service(DOMAIN, SERVICE_RESET_SEEN_STATUS)
    assert hass.services.has_service(DOMAIN, SERVICE_SCAN_MEDIA)


async def test_sensors_creation(hass, mock_db_manager, mock_media_scanner):
    """Test that the sensors are created correctly."""
    config = await init_integration(hass)
    
    # Check that the sensors are created
    sensor_selected = hass.states.get(f"sensor.selected_image")
    sensor_count = hass.states.get(f"sensor.total_images")
    sensor_unseen = hass.states.get(f"sensor.unseen_images")
    
    assert sensor_selected
    assert sensor_count
    assert sensor_unseen


async def test_service_next_image(hass, init_integration, mock_db_manager):
    """Test the next_image service."""
    await hass.services.async_call(
        DOMAIN, SERVICE_NEXT_IMAGE, {}, blocking=True
    )
    
    # Verify that the coordinator's refresh method was called
    # This is done through the show_next_image method
    coordinator = list(hass.data[DOMAIN].values())[0]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_service_previous_image(hass, init_integration, mock_db_manager):
    """Test the previous_image service."""
    coordinator = list(hass.data[DOMAIN].values())[0]["coordinator"]
    coordinator._current_media_id = 1  # Set current media ID
    
    # Mock the previous media
    previous_media = {
        "id": 2,
        "album_id": 1,
        "filename": "sunset.jpg",
        "album_name": "vacation",
        "album_path": "/media/photos/2020-01-vacation",
        "year": 2020,
        "month": 1,
        "extension": ".jpg",
        "is_video": False,
        "last_shown": "2023-04-10T12:00:00"
    }
    mock_db_manager.get_previously_shown_media.return_value = previous_media
    
    await hass.services.async_call(
        DOMAIN, SERVICE_PREVIOUS_IMAGE, {}, blocking=True
    )
    
    # Verify that the get_previously_shown_media method was called
    mock_db_manager.get_previously_shown_media.assert_called_once()
    
    # Verify that the current_media_id was updated
    assert coordinator._current_media_id == 2


async def test_service_set_album_filter(hass, init_integration, mock_db_manager):
    """Test the set_album_filter service."""
    albums = [
        {"id": 1, "name": "vacation"},
        {"id": 2, "name": "birthday"},
    ]
    mock_db_manager.get_albums.return_value = albums
    
    await hass.services.async_call(
        DOMAIN, SERVICE_SET_ALBUM_FILTER, {ATTR_ALBUM_NAME: "vacation"}, blocking=True
    )
    
    # Verify that the album filter was set
    coordinator = list(hass.data[DOMAIN].values())[0]["coordinator"]
    assert coordinator._album_filter == 1


async def test_service_clear_album_filter(hass, init_integration, mock_db_manager):
    """Test the clear_album_filter service."""
    coordinator = list(hass.data[DOMAIN].values())[0]["coordinator"]
    coordinator._album_filter = 1  # Set album filter
    
    await hass.services.async_call(
        DOMAIN, SERVICE_CLEAR_ALBUM_FILTER, {}, blocking=True
    )
    
    # Verify that the album filter was cleared
    assert coordinator._album_filter is None


async def test_service_set_time_range(hass, init_integration, mock_db_manager):
    """Test the set_time_range service."""
    time_range_data = {
        ATTR_TIME_RANGE_START_YEAR: 2020,
        ATTR_TIME_RANGE_START_MONTH: 1,
        ATTR_TIME_RANGE_END_YEAR: 2022,
        ATTR_TIME_RANGE_END_MONTH: 12,
    }
    
    await hass.services.async_call(
        DOMAIN, SERVICE_SET_TIME_RANGE, time_range_data, blocking=True
    )
    
    # Verify that the time range was set
    coordinator = list(hass.data[DOMAIN].values())[0]["coordinator"]
    assert coordinator._time_range["start_year"] == 2020
    assert coordinator._time_range["start_month"] == 1
    assert coordinator._time_range["end_year"] == 2022
    assert coordinator._time_range["end_month"] == 12


async def test_service_clear_time_range(hass, init_integration, mock_db_manager):
    """Test the clear_time_range service."""
    coordinator = list(hass.data[DOMAIN].values())[0]["coordinator"]
    coordinator._time_range = {
        "start_year": 2020,
        "start_month": 1,
        "end_year": 2022,
        "end_month": 12,
    }
    
    await hass.services.async_call(
        DOMAIN, SERVICE_CLEAR_TIME_RANGE, {}, blocking=True
    )
    
    # Verify that the time range was cleared
    assert coordinator._time_range["start_year"] is None
    assert coordinator._time_range["start_month"] is None
    assert coordinator._time_range["end_year"] is None
    assert coordinator._time_range["end_month"] is None


async def test_service_reset_seen_status(hass, init_integration, mock_db_manager):
    """Test the reset_seen_status service."""
    await hass.services.async_call(
        DOMAIN, SERVICE_RESET_SEEN_STATUS, {}, blocking=True
    )
    
    # Verify that the reset_seen_status method was called
    mock_db_manager.reset_seen_status.assert_called_once()


async def test_service_scan_media(hass, init_integration, mock_media_scanner):
    """Test the scan_media service."""
    await hass.services.async_call(
        DOMAIN, SERVICE_SCAN_MEDIA, {}, blocking=True
    )
    
    # Verify that the scan method was called
    mock_media_scanner.scan.assert_called_once()