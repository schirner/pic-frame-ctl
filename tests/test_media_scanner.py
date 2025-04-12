"""Test Picture Frame Controller media scanner."""
import os
import re
from unittest.mock import patch, MagicMock, mock_open, call

import pytest

from custom_components.picture_frame_controller.media_scanner import MediaScanner, ALBUM_PATTERN
from custom_components.picture_frame_controller.const import (
    PATH_CURRENT_LEVEL_ONLY,
    PATH_RECURSIVE,
)


def test_album_pattern():
    """Test the album pattern regex."""
    # Test valid patterns
    assert ALBUM_PATTERN.match("2020-01-vacation")
    assert ALBUM_PATTERN.match("2021_06_birthday")
    
    # Extract parts
    match = ALBUM_PATTERN.match("2020-01-vacation")
    assert match.group(1) == "2020"
    assert match.group(2) == "01"
    assert match.group(3) == "vacation"
    
    match = ALBUM_PATTERN.match("2021_06_birthday")
    assert match.group(1) == "2021"
    assert match.group(2) == "06"
    assert match.group(3) == "birthday"
    
    # Test invalid patterns
    assert not ALBUM_PATTERN.match("2020-vacation")  # Missing month
    assert not ALBUM_PATTERN.match("20-01-vacation")  # Year not 4 digits
    assert not ALBUM_PATTERN.match("2020-1-vacation")  # Month not 2 digits
    assert not ALBUM_PATTERN.match("vacation-photos")  # No date format


def test_scanner_init(hass, mock_db_manager):
    """Test initializing the media scanner."""
    media_paths = ["/test/path/**", "/another/path/*"]
    exclude_patterns = ["^\\.", "^tmp_"]
    image_extensions = [".jpg", ".png"]
    video_extensions = [".mp4", ".mov"]
    
    scanner = MediaScanner(
        hass,
        mock_db_manager,
        media_paths,
        exclude_patterns,
        image_extensions,
        video_extensions
    )
    
    assert scanner._media_paths == media_paths
    assert len(scanner._exclude_patterns) == 2
    assert scanner._image_extensions == [".jpg", ".png"]
    assert scanner._video_extensions == [".mp4", ".mov"]


def test_scanner_should_exclude():
    """Test the exclude pattern matching."""
    scanner = MediaScanner(
        MagicMock(),
        MagicMock(),
        [],
        ["^\\.", "^tmp_", "backup$"]
    )
    
    assert scanner._should_exclude(".hidden")
    assert scanner._should_exclude("tmp_folder")
    assert scanner._should_exclude("files_backup")
    assert not scanner._should_exclude("photos")
    assert not scanner._should_exclude("2020-01-vacation")


@patch("os.path.isdir")
def test_scanner_scan_paths(mock_isdir, hass, mock_db_manager):
    """Test scanning different path types."""
    mock_isdir.return_value = True
    
    scanner = MediaScanner(
        hass,
        mock_db_manager,
        [
            "/photos/recursive/**",
            "/photos/current/*",
            "/photos/regular"
        ]
    )
    
    with patch.object(scanner, "_scan_recursive") as mock_scan_recursive, \
         patch.object(scanner, "_scan_current_level") as mock_scan_current:
        
        mock_scan_recursive.return_value = [({}, [])]
        mock_scan_current.return_value = [({}, [])]
        
        scanner.scan()
        
        # Check that the correct scan method was called for each path type
        mock_scan_recursive.assert_has_calls([
            call("/photos/recursive"),
            call("/photos/regular")
        ])
        
        mock_scan_current.assert_called_once_with("/photos/current")


@patch("os.walk")
@patch("os.path.isdir")
def test_scanner_scan_recursive(mock_isdir, mock_walk, hass, mock_db_manager):
    """Test recursive directory scanning."""
    mock_isdir.return_value = True
    
    # Mock os.walk to return a directory structure
    mock_walk.return_value = [
        # root, dirs, files
        ("/photos", ["2020-01-vacation", "2021-06-birthday", ".hidden"], []),
        ("/photos/2020-01-vacation", [], ["beach.jpg", "sunset.jpg", "video.mp4"]),
        ("/photos/2021-06-birthday", [], ["cake.jpg", "party.mp4"]),
        ("/photos/.hidden", [], ["secret.jpg"])
    ]
    
    scanner = MediaScanner(
        hass,
        mock_db_manager,
        ["/photos/**"],
        ["^\\."]  # Exclude hidden directories
    )
    
    with patch.object(scanner, "_process_album_folder") as mock_process:
        # Return values for the two valid albums
        mock_process.side_effect = [
            ({"id": 1, "name": "vacation"}, [{"id": 1}, {"id": 2}, {"id": 3}]),
            ({"id": 2, "name": "birthday"}, [{"id": 4}, {"id": 5}])
        ]
        
        album_count, media_count = scanner.scan()
        
        # Verify correct albums processed (hidden one skipped)
        assert mock_process.call_count == 2
        mock_process.assert_has_calls([
            call("/photos/2020-01-vacation"),
            call("/photos/2021-06-birthday")
        ])
        
        # Check correct counts returned
        assert album_count == 2
        assert media_count == 5


@patch("os.scandir")
@patch("os.path.isdir")
def test_scanner_scan_current_level(mock_isdir, mock_scandir, hass, mock_db_manager):
    """Test scanning current level only."""
    mock_isdir.return_value = True
    
    # Create mock directory entries
    vacation_entry = MagicMock()
    vacation_entry.name = "2020-01-vacation"
    vacation_entry.is_dir.return_value = True
    vacation_entry.path = "/photos/2020-01-vacation"
    
    birthday_entry = MagicMock()
    birthday_entry.name = "2021-06-birthday"
    birthday_entry.is_dir.return_value = True
    birthday_entry.path = "/photos/2021-06-birthday"
    
    hidden_entry = MagicMock()
    hidden_entry.name = ".hidden"
    hidden_entry.is_dir.return_value = True
    hidden_entry.path = "/photos/.hidden"
    
    file_entry = MagicMock()
    file_entry.name = "info.txt"
    file_entry.is_dir.return_value = False
    file_entry.path = "/photos/info.txt"
    
    mock_scandir.return_value = [vacation_entry, birthday_entry, hidden_entry, file_entry]
    
    scanner = MediaScanner(
        hass,
        mock_db_manager,
        ["/photos/*"],
        ["^\\."]  # Exclude hidden directories
    )
    
    with patch.object(scanner, "_process_album_folder") as mock_process:
        # Return values for the two valid albums
        mock_process.side_effect = [
            ({"id": 1, "name": "vacation"}, [{"id": 1}, {"id": 2}]),
            ({"id": 2, "name": "birthday"}, [{"id": 3}])
        ]
        
        album_count, media_count = scanner.scan()
        
        # Verify correct albums processed (hidden one and file skipped)
        assert mock_process.call_count == 2
        mock_process.assert_has_calls([
            call("/photos/2020-01-vacation"),
            call("/photos/2021-06-birthday")
        ])
        
        # Check correct counts returned
        assert album_count == 2
        assert media_count == 3


@patch("os.scandir")
def test_scanner_process_album_folder(mock_scandir, hass, mock_db_manager):
    """Test processing an album folder."""
    # Mock album path
    album_path = "/photos/2020-01-vacation"
    
    # Mock files in the album
    beach_file = MagicMock()
    beach_file.name = "beach.jpg"
    beach_file.is_file.return_value = True
    beach_file.path = f"{album_path}/beach.jpg"
    
    sunset_file = MagicMock()
    sunset_file.name = "sunset.jpg"
    sunset_file.is_file.return_value = True
    sunset_file.path = f"{album_path}/sunset.jpg"
    
    video_file = MagicMock()
    video_file.name = "party.mp4"
    video_file.is_file.return_value = True
    video_file.path = f"{album_path}/party.mp4"
    
    subdir = MagicMock()
    subdir.name = "thumbs"
    subdir.is_file.return_value = False
    
    # Return the mock files when scanning the album folder
    mock_scandir.return_value = [beach_file, sunset_file, video_file, subdir]
    
    # Configure database manager mock
    mock_db_manager.add_album.return_value = 1
    mock_db_manager.add_media_file.side_effect = [1, 2, 3]
    
    # Create scanner with default settings
    scanner = MediaScanner(
        hass,
        mock_db_manager,
        ["/photos/**"]
    )
    
    # Process the album folder
    album_info, media_files = scanner._process_album_folder(album_path)
    
    # Check album was added correctly
    mock_db_manager.add_album.assert_called_once_with(
        album_path, "vacation", 2020, 1
    )
    
    # Check media files were added
    assert mock_db_manager.add_media_file.call_count == 3
    mock_db_manager.add_media_file.assert_has_calls([
        call(1, "beach.jpg", ".jpg", False),
        call(1, "sunset.jpg", ".jpg", False),
        call(1, "party.mp4", ".mp4", True)
    ])
    
    # Check returned album info
    assert album_info["id"] == 1
    assert album_info["name"] == "vacation"
    assert album_info["year"] == 2020
    assert album_info["month"] == 1
    
    # Check returned media files
    assert len(media_files) == 3
    assert media_files[0]["id"] == 1
    assert media_files[0]["filename"] == "beach.jpg"
    assert media_files[0]["is_video"] == False
    assert media_files[2]["id"] == 3
    assert media_files[2]["filename"] == "party.mp4"
    assert media_files[2]["is_video"] == True