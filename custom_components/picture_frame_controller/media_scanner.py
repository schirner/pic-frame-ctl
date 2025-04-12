"""Media scanner for the picture frame controller integration."""
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple, Any

from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_IMAGE_EXTENSIONS,
    DEFAULT_VIDEO_EXTENSIONS,
    PATH_CURRENT_LEVEL_ONLY,
    PATH_RECURSIVE,
)
from .database_manager import DatabaseManager

_LOGGER = logging.getLogger(__name__)

# Pattern to extract album info: YYYY[-_]MM[-_]NAME
ALBUM_PATTERN = re.compile(r"^(\d{4})[-_](\d{2})[-_](.*)$")

class MediaScanner:
    """Class to scan media directories and build database."""

    def __init__(self, 
                hass: HomeAssistant, 
                db_manager: DatabaseManager,
                media_paths: List[str],
                exclude_patterns: Optional[List[str]] = None,
                image_extensions: Optional[List[str]] = None,
                video_extensions: Optional[List[str]] = None):
        """Initialize the media scanner."""
        self.hass = hass
        self._db_manager = db_manager
        self._media_paths = media_paths
        self._exclude_patterns = [re.compile(pattern) for pattern in (exclude_patterns or [])]
        self._image_extensions = [ext.lower() for ext in (image_extensions or DEFAULT_IMAGE_EXTENSIONS)]
        self._video_extensions = [ext.lower() for ext in (video_extensions or DEFAULT_VIDEO_EXTENSIONS)]

    def scan(self) -> Tuple[int, int]:
        """Scan media directories and build database."""
        album_count = 0
        media_count = 0

        for path in self._media_paths:
            # Determine scan type based on path suffix
            recursive = True
            base_path = path

            if path.endswith(PATH_RECURSIVE):
                base_path = path[:-len(PATH_RECURSIVE)]
                recursive = True
            elif path.endswith(PATH_CURRENT_LEVEL_ONLY):
                base_path = path[:-len(PATH_CURRENT_LEVEL_ONLY)]
                recursive = False

            # Ensure the base path exists
            if not os.path.isdir(base_path):
                _LOGGER.warning("Media path does not exist: %s", base_path)
                continue

            # Start scanning for albums
            _LOGGER.info("Scanning for albums in %s (recursive: %s)", base_path, recursive)
            
            if recursive:
                for album, album_media in self._scan_recursive(base_path):
                    album_count += 1
                    media_count += len(album_media)
            else:
                for album, album_media in self._scan_current_level(base_path):
                    album_count += 1
                    media_count += len(album_media)

        _LOGGER.info("Scan complete: %d albums, %d media files", album_count, media_count)
        return album_count, media_count

    def _scan_recursive(self, base_path: str) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
        """Recursively scan directories for album folders."""
        results = []
        
        for root, dirs, _ in os.walk(base_path):
            # Skip directories that match exclude patterns
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]
            
            # Check if current directory is a leaf/album directory
            if not dirs:  # No subdirectories, this is a leaf/album folder
                album_info, media_files = self._process_album_folder(root)
                if album_info and media_files:
                    results.append((album_info, media_files))
        
        return results

    def _scan_current_level(self, base_path: str) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
        """Scan only the current level for album folders."""
        results = []
        
        try:
            # Get all immediate subdirectories
            for entry in os.scandir(base_path):
                if entry.is_dir() and not self._should_exclude(entry.name):
                    album_info, media_files = self._process_album_folder(entry.path)
                    if album_info and media_files:
                        results.append((album_info, media_files))
        except OSError as err:
            _LOGGER.error("Error scanning directory %s: %s", base_path, err)
        
        return results

    def _process_album_folder(self, folder_path: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process a potential album folder, extract album info and media files."""
        folder_name = os.path.basename(folder_path)
        media_files = []
        
        # Extract album info from folder name
        album_name = folder_name
        year = None
        month = None
        
        match = ALBUM_PATTERN.match(folder_name)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            album_name = match.group(3)
        
        # Add album to database
        album_id = self._db_manager.add_album(folder_path, album_name, year, month)
        
        if album_id == -1:
            _LOGGER.error("Failed to add album to database: %s", folder_path)
            return None, []
        
        # Scan for media files in the album folder
        try:
            for entry in os.scandir(folder_path):
                if entry.is_file():
                    file_ext = os.path.splitext(entry.name)[1].lower()
                    
                    if file_ext in self._image_extensions:
                        media_id = self._db_manager.add_media_file(
                            album_id, entry.name, file_ext, is_video=False
                        )
                        if media_id != -1:
                            media_files.append({
                                "id": media_id,
                                "path": entry.path,
                                "filename": entry.name,
                                "is_video": False
                            })
                    elif file_ext in self._video_extensions:
                        media_id = self._db_manager.add_media_file(
                            album_id, entry.name, file_ext, is_video=True
                        )
                        if media_id != -1:
                            media_files.append({
                                "id": media_id,
                                "path": entry.path,
                                "filename": entry.name,
                                "is_video": True
                            })
        except OSError as err:
            _LOGGER.error("Error scanning album folder %s: %s", folder_path, err)
        
        if not media_files:
            _LOGGER.warning("No media files found in album: %s", folder_path)
        
        return {"id": album_id, "path": folder_path, "name": album_name, "year": year, "month": month}, media_files

    def _should_exclude(self, dir_name: str) -> bool:
        """Check if a directory should be excluded based on patterns."""
        for pattern in self._exclude_patterns:
            if pattern.search(dir_name):
                return True
        return False