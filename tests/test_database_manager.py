"""Test Picture Frame Controller database manager."""
import os
import sqlite3
from unittest.mock import patch, MagicMock, mock_open

import pytest
from datetime import datetime

from custom_components.picture_frame_controller.database_manager import DatabaseManager


@pytest.fixture
def mock_sqlite():
    """Mock SQLite connection and cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.row_factory = None

    with patch('sqlite3.connect', return_value=mock_conn):
        yield mock_conn, mock_cursor


@pytest.fixture
def setup_test_db():
    """Create a temporary in-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create schema
    cursor = conn.cursor()
    
    # Create schema version table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY,
            version INTEGER NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    
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
    
    # Insert initial schema version
    cursor.execute(
        "INSERT INTO schema_version (version, updated_at) VALUES (?, ?)",
        (1, datetime.now().isoformat())
    )
    
    # Insert test data
    # Albums
    cursor.execute(
        """
        INSERT INTO albums (id, path, name, year, month, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, "/media/photos/2020-01-vacation", "vacation", 2020, 1, datetime.now().isoformat())
    )
    
    cursor.execute(
        """
        INSERT INTO albums (id, path, name, year, month, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (2, "/media/photos/2021-06-birthday", "birthday", 2021, 6, datetime.now().isoformat())
    )
    
    cursor.execute(
        """
        INSERT INTO albums (id, path, name, year, month, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (3, "/media/photos/family_photos", "family_photos", None, None, datetime.now().isoformat())
    )
    
    # Media files
    cursor.execute(
        """
        INSERT INTO media_files (id, album_id, filename, extension, is_video, seen, last_shown)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (1, 1, "beach.jpg", ".jpg", 0, 0, None)
    )
    
    cursor.execute(
        """
        INSERT INTO media_files (id, album_id, filename, extension, is_video, seen, last_shown)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (2, 1, "sunset.jpg", ".jpg", 0, 0, None)
    )
    
    cursor.execute(
        """
        INSERT INTO media_files (id, album_id, filename, extension, is_video, seen, last_shown)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (3, 2, "cake.jpg", ".jpg", 0, 0, None)
    )
    
    cursor.execute(
        """
        INSERT INTO media_files (id, album_id, filename, extension, is_video, seen, last_shown)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (4, 2, "party.mp4", ".mp4", 1, 0, None)
    )
    
    cursor.execute(
        """
        INSERT INTO media_files (id, album_id, filename, extension, is_video, seen, last_shown)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (5, 3, "family.jpg", ".jpg", 0, 0, None)
    )
    
    conn.commit()
    
    yield conn
    
    conn.close()


@patch('os.path.exists')
@patch('os.path.join')
def test_db_setup_new_database(mock_join, mock_exists, mock_sqlite):
    """Test database setup when the database doesn't exist."""
    mock_conn, mock_cursor = mock_sqlite
    mock_exists.return_value = False
    mock_join.return_value = "/config/picture_frame_controller.db"
    
    # Create a mock HASS instead of using the real one
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/config"
    
    # Create DB manager
    db_manager = DatabaseManager(mock_hass)
    
    # Check that create tables was called
    mock_cursor.execute.assert_any_call("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY,
                version INTEGER NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
    
    # Check initial schema version was inserted - verify first parameter only
    # since the datetime value is dynamic
    called_with_insert = False
    for call_args in mock_cursor.execute.call_args_list:
        args, kwargs = call_args
        if len(args) >= 1 and "INSERT INTO schema_version" in args[0]:
            called_with_insert = True
            break
    
    assert called_with_insert, "Missing INSERT INTO schema_version call"


@patch('os.path.exists')
@patch('os.path.join')
def test_db_setup_existing_database(mock_join, mock_exists, mock_sqlite):
    """Test database setup when the database already exists."""
    mock_conn, mock_cursor = mock_sqlite
    mock_exists.return_value = True
    mock_join.return_value = "/config/picture_frame_controller.db"
    
    # Create a mock HASS instead of using the real one
    mock_hass = MagicMock()
    mock_hass.config.path.return_value = "/config"
    
    # Mock cursor fetchone response for version check
    mock_cursor.fetchone.return_value = {"version": 1}
    
    # Create DB manager
    db_manager = DatabaseManager(mock_hass)
    
    # Check that version was checked
    mock_cursor.execute.assert_any_call("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
    mock_cursor.fetchone.assert_called_once()


def test_add_album(setup_test_db):
    """Test adding an album to the database."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Add a new album
        new_album_id = db_manager.add_album(
            "/media/photos/2022-12-christmas", "christmas", 2022, 12
        )
        
        # Check album was added
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM albums WHERE id = ?", (new_album_id,))
        album = cursor.fetchone()
        
        assert album is not None
        assert album["path"] == "/media/photos/2022-12-christmas"
        assert album["name"] == "christmas"
        assert album["year"] == 2022
        assert album["month"] == 12


def test_add_media_file(setup_test_db):
    """Test adding a media file to the database."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Add a new media file
        album_id = 1  # Use existing album
        new_media_id = db_manager.add_media_file(
            album_id, "mountains.jpg", ".jpg", False
        )
        
        # Check media was added
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_files WHERE id = ?", (new_media_id,))
        media = cursor.fetchone()
        
        assert media is not None
        assert media["album_id"] == album_id
        assert media["filename"] == "mountains.jpg"
        assert media["extension"] == ".jpg"
        assert media["is_video"] == 0
        assert media["seen"] == 0
        assert media["last_shown"] is None


def test_get_media_count(setup_test_db):
    """Test getting the media count."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        count = db_manager.get_media_count()
        assert count == 5  # We inserted 5 media files in setup


def test_get_unseen_count(setup_test_db):
    """Test getting the unseen media count."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Initially all files are unseen
        count_all = db_manager.get_unseen_count()
        assert count_all == 5
        
        count_album = db_manager.get_unseen_count(album_id=1)
        assert count_album == 2  # Album 1 has 2 files
        
        # Mark one media as seen
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE media_files SET seen = 1 WHERE id = 1"
        )
        conn.commit()
        
        # Check counts again
        count_all_after = db_manager.get_unseen_count()
        assert count_all_after == 4  # One file marked seen
        
        count_album_after = db_manager.get_unseen_count(album_id=1)
        assert count_album_after == 1  # Album 1 has 1 unseen file now


def test_get_random_unseen_media(setup_test_db):
    """Test getting random unseen media."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Get a random file
        media = db_manager.get_random_unseen_media()
        assert media is not None
        assert media["id"] in [1, 2, 3, 4, 5]  # One of our test files
        
        # Get a random file from a specific album
        media_album = db_manager.get_random_unseen_media(album_id=2)
        assert media_album is not None
        assert media_album["album_id"] == 2
        
        # Mark all media as seen
        cursor = conn.cursor()
        cursor.execute("UPDATE media_files SET seen = 1")
        conn.commit()
        
        # No unseen media should be found
        no_media = db_manager.get_random_unseen_media()
        assert no_media is None


def test_mark_media_as_seen(setup_test_db):
    """Test marking media as seen."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Mark media as seen
        db_manager.mark_media_as_seen(1)
        
        # Check media was marked as seen
        cursor = conn.cursor()
        cursor.execute("SELECT seen, last_shown FROM media_files WHERE id = 1")
        media = cursor.fetchone()
        
        assert media["seen"] == 1
        assert media["last_shown"] is not None


def test_get_previously_shown_media(setup_test_db):
    """Test getting previously shown media."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Mark some media as seen with timestamps
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    one_hour_ago = (datetime.now().replace(hour=datetime.now().hour-1)).isoformat()
    two_hours_ago = (datetime.now().replace(hour=datetime.now().hour-2)).isoformat()
    
    cursor.execute(
        "UPDATE media_files SET seen = 1, last_shown = ? WHERE id = ?",
        (one_hour_ago, 1)
    )
    cursor.execute(
        "UPDATE media_files SET seen = 1, last_shown = ? WHERE id = ?",
        (now, 2)
    )
    cursor.execute(
        "UPDATE media_files SET seen = 1, last_shown = ? WHERE id = ?",
        (two_hours_ago, 3)
    )
    conn.commit()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Get previously shown media (should be the one shown 1 hour ago, ID 1)
        previous = db_manager.get_previously_shown_media(current_media_id=2)
        assert previous is not None
        assert previous["id"] == 1  # The second most recent


def test_reset_seen_status(setup_test_db):
    """Test resetting seen status."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Mark all media as seen
    cursor = conn.cursor()
    cursor.execute("UPDATE media_files SET seen = 1, last_shown = ?", (datetime.now().isoformat(),))
    conn.commit()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Get unseen count (should be 0)
        count_before = db_manager.get_unseen_count()
        assert count_before == 0
        
        # Reset seen status
        db_manager.reset_seen_status()
        
        # Check all media is now unseen
        count_after = db_manager.get_unseen_count()
        assert count_after == 5
        
        # Mark album 1 as seen again
        cursor.execute("UPDATE media_files SET seen = 1, last_shown = ? WHERE album_id = 1", 
                      (datetime.now().isoformat(),))
        conn.commit()
        
        # Reset just album 1
        db_manager.reset_seen_status(album_id=1)
        
        # Check album 1 is unseen
        count_album = db_manager.get_unseen_count(album_id=1)
        assert count_album == 2


def test_time_range_filter(setup_test_db):
    """Test the time range filter for getting media."""
    conn = setup_test_db
    
    # Create a mock hass
    hass = MagicMock()
    
    # Create DB manager with the test database
    with patch('sqlite3.connect', return_value=conn), \
         patch('os.path.exists', return_value=True):
        db_manager = DatabaseManager(hass)
        
        # Get media from 2020
        media_2020 = db_manager.get_random_unseen_media(
            start_year=2020, start_month=1, 
            end_year=2020, end_month=12
        )
        assert media_2020 is not None
        assert media_2020["year"] == 2020
        
        # Get media from 2021
        media_2021 = db_manager.get_random_unseen_media(
            start_year=2021, start_month=1, 
            end_year=2021, end_month=12
        )
        assert media_2021 is not None
        assert media_2021["year"] == 2021
        
        # Get media from 2019 (should be None, we don't have any)
        media_2019 = db_manager.get_random_unseen_media(
            start_year=2019, start_month=1, 
            end_year=2019, end_month=12
        )
        assert media_2019 is None
        
        # Reset seen status for time range
        db_manager.reset_seen_status(
            time_range=True,
            start_year=2021, start_month=1,
            end_year=2021, end_month=12
        )
        
        # Check that album 2 (from 2021) is now reset
        count_album_2 = db_manager.get_unseen_count(album_id=2)
        assert count_album_2 == 2