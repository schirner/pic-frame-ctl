"""Test configuration for the Picture Frame Controller component."""
import os
import pytest
from unittest.mock import patch, MagicMock

from homeassistant.setup import async_setup_component
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PLATFORM
from custom_components.picture_frame_controller.const import DOMAIN, CONF_MEDIA_PATHS


@pytest.fixture
def hass(loop):
    """Set up a Home Assistant instance for testing."""
    hass = HomeAssistant()
    # Set up as if the component got set up via config flow
    hass.data[DOMAIN] = {}
    
    yield hass
    
    # Clean up
    hass.stop()


@pytest.fixture
def mock_db_manager():
    """Patch the database manager."""
    with patch('custom_components.picture_frame_controller.database_manager.DatabaseManager') as mock_db_manager_class:
        mock_instance = MagicMock()
        mock_db_manager_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_media_scanner():
    """Patch the media scanner."""
    with patch('custom_components.picture_frame_controller.media_scanner.MediaScanner') as mock_scanner_class:
        mock_instance = MagicMock()
        mock_scanner_class.return_value = mock_instance
        mock_instance.scan.return_value = (5, 100)  # 5 albums, 100 media files
        yield mock_instance


@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists for testing path validation."""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True  # Default to existing paths
        yield mock_exists


@pytest.fixture
def mock_os_scandir():
    """Mock os.scandir for testing directory scanning."""
    with patch('os.scandir') as mock_scandir:
        mock_instance = MagicMock()
        mock_scandir.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def test_media_data():
    """Return test media data for database testing."""
    albums = [
        {
            "id": 1, 
            "path": "/media/photos/2020-01-vacation",
            "name": "vacation",
            "year": 2020,
            "month": 1,
            "created_at": "2023-01-01T00:00:00"
        },
        {
            "id": 2,
            "path": "/media/photos/2021-06-birthday",
            "name": "birthday",
            "year": 2021,
            "month": 6,
            "created_at": "2023-01-01T00:00:00"
        },
        {
            "id": 3,
            "path": "/media/photos/family_photos",
            "name": "family_photos",
            "year": None,
            "month": None,
            "created_at": "2023-01-01T00:00:00"
        }
    ]
    
    media_files = [
        {
            "id": 1,
            "album_id": 1,
            "filename": "beach.jpg",
            "extension": ".jpg",
            "is_video": 0,
            "seen": 0,
            "last_shown": None
        },
        {
            "id": 2,
            "album_id": 1,
            "filename": "sunset.jpg",
            "extension": ".jpg",
            "is_video": 0,
            "seen": 0,
            "last_shown": None
        },
        {
            "id": 3,
            "album_id": 2,
            "filename": "cake.jpg",
            "extension": ".jpg",
            "is_video": 0,
            "seen": 0,
            "last_shown": None
        },
        {
            "id": 4,
            "album_id": 2,
            "filename": "party.mp4",
            "extension": ".mp4",
            "is_video": 1,
            "seen": 0,
            "last_shown": None
        },
        {
            "id": 5,
            "album_id": 3,
            "filename": "family.jpg",
            "extension": ".jpg",
            "is_video": 0,
            "seen": 0,
            "last_shown": None
        }
    ]
    
    return {
        "albums": albums,
        "media_files": media_files
    }


@pytest.fixture
async def init_integration(hass, mock_db_manager, mock_media_scanner):
    """Set up the Picture Frame Controller integration in Home Assistant."""
    # Mock configuration for the component
    config = {
        DOMAIN: {
            CONF_MEDIA_PATHS: ["/media/photos/**"],
        }
    }
    
    # Set up mocked database responses
    mock_db_manager.get_media_count.return_value = 5
    mock_db_manager.get_unseen_count.return_value = 5
    mock_db_manager.get_random_unseen_media.return_value = {
        "id": 1,
        "album_id": 1,
        "filename": "beach.jpg",
        "album_name": "vacation",
        "album_path": "/media/photos/2020-01-vacation",
        "year": 2020,
        "month": 1,
        "extension": ".jpg",
        "is_video": False
    }
    
    # Set up the component
    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    
    return config