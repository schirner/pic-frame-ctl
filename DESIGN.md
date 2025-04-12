# Picture Frame Controller - Design Documentation

## Architecture Overview

The Picture Frame Controller is a Home Assistant custom component designed to manage digital picture frames by controlling the display of images and videos from a collection of media files. The component is built with a modular architecture consisting of several key components:

1. **Database Manager**: Core persistence layer that tracks albums, media files, and viewing history
2. **Media Scanner**: Service that analyzes filesystem directories to discover media files
3. **Coordinator**: Central controller that manages state and coordinates updates
4. **Sensors**: Entities that expose state to Home Assistant for dashboard use and automation
5. **Services**: Interface for external control of the component
6. **Frontend**: Custom Lovelace card for user interaction

## Database Design

The component uses SQLite for data storage with a normalized schema:

### Schema Version Table
Tracks database migrations for future updates.
```
schema_version (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
```

### Albums Table
Stores information about media folders.
```
albums (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    year INTEGER,
    month INTEGER,
    created_at TIMESTAMP NOT NULL
)
```

### Media Files Table
Stores information about individual media files.
```
media_files (
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
```

The database design follows these principles:
- Each album has a unique path
- Media files are associated with exactly one album
- Viewing history is tracked per media file
- Album dates are extracted from folder naming patterns

## Media Scanner

The media scanner processes directories to identify albums and media files:

1. **Path Handling**: Supports both recursive (`/**`) and current-level-only (`/*`) directory scanning
2. **Album Detection**: Uses regex pattern matching to extract year and month from folder names
3. **Media Classification**: Identifies images and videos based on file extensions
4. **Filtering**: Supports regex-based exclusion patterns to skip specific folders

## Coordinator System

The coordinator manages the component state and provides business logic:

1. **Data Consistency**: Ensures database state matches sensor states
2. **Filtering Logic**: Implements album and date range filtering
3. **Navigation**: Handles next/previous image selection based on filters
4. **Update Scheduling**: Controls sensor update timing

## Services API

The component provides the following services:

- `next_image`: Show the next random unseen image
- `previous_image`: Show the previously shown image
- `set_album_filter`: Filter to show only images from a specific album
- `clear_album_filter`: Clear the album filter
- `set_time_range`: Filter images by date range
- `clear_time_range`: Clear the date range filter
- `reset_seen_status`: Reset the seen status for all media
- `scan_media`: Re-scan media directories

## Sensor Implementation

Three main sensors are implemented:

1. `selected_image`: The current image being displayed
2. `count_image`: Total count of media files
3. `count_unseen`: Count of unseen media files

## Frontend Card

The custom Lovelace card provides:

1. Image/video display with controls
2. Album and date filtering UI
3. Navigation buttons
4. Media information display

## Event Flow

1. **Initial Setup**: Config flow validates paths and creates config entry
2. **Initialization**: Component creates database manager, media scanner, and coordinator
3. **Media Scan**: Scanner identifies albums and media files
4. **State Management**: Coordinator selects initial image and updates sensors
5. **User Interaction**: User controls via UI card or services
6. **Updates**: Sensors update when state changes

## Configuration Options

- `media_paths`: List of paths to scan for media
- `exclude_pattern`: List of regex patterns for directories to exclude
- `update_interval`: How frequently to update the displayed image
- `image_extensions`: Supported image file extensions
- `video_extensions`: Supported video file extensions