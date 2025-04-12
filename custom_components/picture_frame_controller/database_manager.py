"""Database manager for the picture frame controller integration."""
import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from homeassistant.core import HomeAssistant

from .const import (
    ATTR_ALBUM_NAME,
    ATTR_MONTH,
    ATTR_YEAR,
    DATABASE_FILENAME,
    DB_VERSION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

class DatabaseManager:
    """Class to manage the SQLite database."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the database manager."""
        self.hass = hass
        self._db_path = os.path.join(hass.config.path(), DATABASE_FILENAME)
        self._conn = None
        self._setup_database()

    def _setup_database(self):
        """Set up the database if it does not exist."""
        db_exists = os.path.exists(self._db_path)
        
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        
        if not db_exists:
            self._create_tables()
        else:
            self._check_version()

    def _create_tables(self):
        """Create the initial database tables."""
        cursor = self._conn.cursor()
        
        # Create schema version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY,
                version INTEGER NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        # Insert initial schema version
        cursor.execute(
            "INSERT INTO schema_version (version, updated_at) VALUES (?, ?)",
            (DB_VERSION, datetime.now().isoformat())
        )
        
        # Create albums table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                year INTEGER,
                month INTEGER,
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create media files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY,
                album_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                extension TEXT NOT NULL,
                is_video INTEGER NOT NULL DEFAULT 0,
                seen INTEGER NOT NULL DEFAULT 0,
                last_shown TIMESTAMP,
                FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE CASCADE,
                UNIQUE(album_id, filename)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_seen ON media_files (seen)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_album ON media_files (album_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_albums_year_month ON albums (year, month)")
        
        self._conn.commit()
        _LOGGER.info("Database tables created successfully")

    def _check_version(self):
        """Check the database schema version and migrate if needed."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row and row["version"] != DB_VERSION:
                self._migrate_database(row["version"])
        except sqlite3.Error as err:
            _LOGGER.error("Error checking database version: %s", err)

    def _migrate_database(self, current_version: int):
        """Migrate database schema to the latest version."""
        _LOGGER.info("Migrating database from version %s to %s", current_version, DB_VERSION)
        
        # Add migration steps as needed in the future
        # Example:
        # if current_version == 1 and DB_VERSION == 2:
        #     cursor = self._conn.cursor()
        #     cursor.execute("ALTER TABLE albums ADD COLUMN new_field TEXT")
        #     self._conn.commit()
        
        # Update the schema version
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO schema_version (version, updated_at) VALUES (?, ?)",
            (DB_VERSION, datetime.now().isoformat())
        )
        self._conn.commit()
        _LOGGER.info("Database migration completed")

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_album(self, path: str, name: str, year: Optional[int] = None, 
                 month: Optional[int] = None) -> int:
        """Add an album to the database."""
        cursor = self._conn.cursor()
        
        try:
            # First check if the album exists
            cursor.execute("SELECT id FROM albums WHERE path = ?", (path,))
            existing_album = cursor.fetchone()
            
            if existing_album:
                # Update the existing album
                cursor.execute(
                    """
                    UPDATE albums SET 
                        name = ?,
                        year = ?,
                        month = ?
                    WHERE path = ?
                    """,
                    (name, year, month, path)
                )
                album_id = existing_album["id"]
            else:
                # Insert a new album
                cursor.execute(
                    """
                    INSERT INTO albums (path, name, year, month, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (path, name, year, month, datetime.now().isoformat())
                )
                album_id = cursor.lastrowid
                
            self._conn.commit()
            return album_id
        except sqlite3.Error as err:
            _LOGGER.error("Error adding album: %s", err)
            self._conn.rollback()
            return -1

    def add_media_file(self, album_id: int, filename: str, extension: str, is_video: bool = False) -> int:
        """Add a media file to the database."""
        cursor = self._conn.cursor()
        
        try:
            # First check if the media file exists
            cursor.execute(
                "SELECT id FROM media_files WHERE album_id = ? AND filename = ?",
                (album_id, filename)
            )
            existing_media = cursor.fetchone()
            
            if existing_media:
                # Return the existing media ID
                return existing_media["id"]
            else:
                # Insert a new media file
                cursor.execute(
                    """
                    INSERT INTO media_files (album_id, filename, extension, is_video)
                    VALUES (?, ?, ?, ?)
                    """,
                    (album_id, filename, extension.lower(), 1 if is_video else 0)
                )
                media_id = cursor.lastrowid
                self._conn.commit()
                return media_id
        except sqlite3.Error as err:
            _LOGGER.error("Error adding media file: %s", err)
            self._conn.rollback()
            return -1

    def get_album_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get album by path."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM albums WHERE path = ?", 
                (path,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except sqlite3.Error as err:
            _LOGGER.error("Error getting album by path: %s", err)
            return None

    def get_albums(self) -> List[Dict[str, Any]]:
        """Get all albums."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM albums ORDER BY year, month, name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as err:
            _LOGGER.error("Error getting albums: %s", err)
            return []

    def get_media_count(self) -> int:
        """Get the total count of media files."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) as count FROM media_files")
            return cursor.fetchone()["count"]
        except sqlite3.Error as err:
            _LOGGER.error("Error getting media count: %s", err)
            return 0

    def get_unseen_count(self, album_id: Optional[int] = None) -> int:
        """Get the count of unseen media files, optionally filtered by album."""
        cursor = self._conn.cursor()
        
        try:
            if album_id is not None:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM media_files WHERE seen = 0 AND album_id = ?",
                    (album_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM media_files WHERE seen = 0")
                
            return cursor.fetchone()["count"]
        except sqlite3.Error as err:
            _LOGGER.error("Error getting unseen count: %s", err)
            return 0

    def get_random_unseen_media(self, album_id: Optional[int] = None, 
                               start_year: Optional[int] = None, 
                               start_month: Optional[int] = None,
                               end_year: Optional[int] = None,
                               end_month: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a random unseen media file with filters."""
        cursor = self._conn.cursor()
        
        try:
            query = """
                SELECT 
                    m.id, m.filename, m.extension, m.is_video,
                    a.id as album_id, a.path as album_path, a.name as album_name, 
                    a.year, a.month
                FROM media_files m
                JOIN albums a ON m.album_id = a.id
                WHERE m.seen = 0
            """
            params = []
            
            # Apply album filter if provided
            if album_id is not None:
                query += " AND m.album_id = ?"
                params.append(album_id)
            
            # Apply time range filter if provided
            if all([start_year, start_month, end_year, end_month]):
                query += """
                    AND (
                        (a.year > ? OR (a.year = ? AND a.month >= ?))
                        AND
                        (a.year < ? OR (a.year = ? AND a.month <= ?))
                    )
                """
                params.extend([start_year, start_year, start_month, 
                              end_year, end_year, end_month])
            
            # Get a random record
            query += " ORDER BY RANDOM() LIMIT 1"
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            
            # If no unseen media is found, return None
            return None
        except sqlite3.Error as err:
            _LOGGER.error("Error getting random unseen media: %s", err)
            return None

    def mark_media_as_seen(self, media_id: int):
        """Mark a media file as seen with timestamp."""
        cursor = self._conn.cursor()
        
        try:
            timestamp = datetime.now().isoformat()
            cursor.execute(
                "UPDATE media_files SET seen = 1, last_shown = ? WHERE id = ?",
                (timestamp, media_id)
            )
            self._conn.commit()
        except sqlite3.Error as err:
            _LOGGER.error("Error marking media as seen: %s", err)
            self._conn.rollback()

    def get_previously_shown_media(self, 
                                  current_media_id: Optional[int] = None, 
                                  album_id: Optional[int] = None,
                                  start_year: Optional[int] = None,
                                  start_month: Optional[int] = None,
                                  end_year: Optional[int] = None,
                                  end_month: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get the previously shown media."""
        cursor = self._conn.cursor()
        
        try:
            query = """
                SELECT 
                    m.id, m.filename, m.extension, m.is_video, m.last_shown,
                    a.id as album_id, a.path as album_path, a.name as album_name, 
                    a.year, a.month
                FROM media_files m
                JOIN albums a ON m.album_id = a.id
                WHERE m.last_shown IS NOT NULL
            """
            params = []
            
            # Skip current media
            if current_media_id is not None:
                query += " AND m.id != ?"
                params.append(current_media_id)
            
            # Apply album filter if provided
            if album_id is not None:
                query += " AND m.album_id = ?"
                params.append(album_id)
            
            # Apply time range filter if provided
            if all([start_year, start_month, end_year, end_month]):
                query += """
                    AND (
                        (a.year > ? OR (a.year = ? AND a.month >= ?))
                        AND
                        (a.year < ? OR (a.year = ? AND a.month <= ?))
                    )
                """
                params.extend([start_year, start_year, start_month, 
                              end_year, end_year, end_month])
            
            # Order by last shown timestamp descending
            query += " ORDER BY m.last_shown DESC LIMIT 1"
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            
            return None
        except sqlite3.Error as err:
            _LOGGER.error("Error getting previously shown media: %s", err)
            return None

    def reset_seen_status(self, album_id: Optional[int] = None, 
                         time_range: bool = False,
                         start_year: Optional[int] = None,
                         start_month: Optional[int] = None,
                         end_year: Optional[int] = None,
                         end_month: Optional[int] = None):
        """Reset seen status for all media or filtered by album/time range."""
        cursor = self._conn.cursor()
        
        try:
            if album_id is not None:
                # Reset for specific album
                cursor.execute(
                    "UPDATE media_files SET seen = 0, last_shown = NULL WHERE album_id = ?",
                    (album_id,)
                )
            elif time_range and all([start_year, start_month, end_year, end_month]):
                # Reset for time range
                cursor.execute("""
                    UPDATE media_files SET seen = 0, last_shown = NULL 
                    WHERE album_id IN (
                        SELECT id FROM albums 
                        WHERE 
                            (year > ? OR (year = ? AND month >= ?))
                            AND
                            (year < ? OR (year = ? AND month <= ?))
                    )
                """, (start_year, start_year, start_month, end_year, end_year, end_month))
            else:
                # Reset all
                cursor.execute("UPDATE media_files SET seen = 0, last_shown = NULL")
                
            self._conn.commit()
        except sqlite3.Error as err:
            _LOGGER.error("Error resetting seen status: %s", err)
            self._conn.rollback()

    def get_album_by_id(self, album_id: int) -> Optional[Dict[str, Any]]:
        """Get album by ID."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except sqlite3.Error as err:
            _LOGGER.error("Error getting album by ID: %s", err)
            return None

    def clear_database(self):
        """Clear all data from the database (used for testing)."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute("DELETE FROM media_files")
            cursor.execute("DELETE FROM albums")
            self._conn.commit()
        except sqlite3.Error as err:
            _LOGGER.error("Error clearing database: %s", err)
            self._conn.rollback()

    def get_media_by_id(self, media_id: int) -> Optional[Dict[str, Any]]:
        """Get media by ID with album information."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    m.id, m.filename, m.extension, m.is_video, m.last_shown,
                    a.id as album_id, a.path as album_path, a.name as album_name, 
                    a.year, a.month
                FROM media_files m
                JOIN albums a ON m.album_id = a.id
                WHERE m.id = ?
            """, (media_id,))
            
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except sqlite3.Error as err:
            _LOGGER.error("Error getting media by ID: %s", err)
            return None