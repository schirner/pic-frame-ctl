"""Constants for the Picture Frame Controller integration."""

DOMAIN = "picture_frame_controller"
NAME = "Picture Frame Controller"

# Configuration
CONF_MEDIA_PATHS = "media_paths"
CONF_EXCLUDE_PATTERN = "exclude_pattern"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_IMAGE_EXTENSIONS = "image_extensions"
CONF_VIDEO_EXTENSIONS = "video_extensions"

# Default values
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
DEFAULT_VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

# Sensors
SENSOR_SELECTED_IMAGE = "selected_image"
SENSOR_COUNT_IMAGE = "count_image" 
SENSOR_COUNT_UNSEEN = "count_unseen"

# Database
DATABASE_FILENAME = "picture_frame_controller.db"
DB_VERSION = 1

# Events
EVENT_IMAGE_CHANGED = f"{DOMAIN}_image_changed"

# Services
SERVICE_NEXT_IMAGE = "next_image"
SERVICE_PREVIOUS_IMAGE = "previous_image"
SERVICE_SET_ALBUM_FILTER = "set_album_filter"
SERVICE_CLEAR_ALBUM_FILTER = "clear_album_filter"
SERVICE_SET_TIME_RANGE = "set_time_range"
SERVICE_CLEAR_TIME_RANGE = "clear_time_range"
SERVICE_RESET_SEEN_STATUS = "reset_seen_status"
SERVICE_SCAN_MEDIA = "scan_media"

# Attributes
ATTR_ALBUM_NAME = "album_name"
ATTR_YEAR = "year"
ATTR_MONTH = "month"
ATTR_MEDIA_PATH = "media_path"
ATTR_LAST_SHOWN = "last_shown"
ATTR_IMAGE_NAME = "image_name"
ATTR_TIME_RANGE_START_YEAR = "start_year"
ATTR_TIME_RANGE_START_MONTH = "start_month"
ATTR_TIME_RANGE_END_YEAR = "end_year"
ATTR_TIME_RANGE_END_MONTH = "end_month"

# Path indicators
PATH_CURRENT_LEVEL_ONLY = "*"
PATH_RECURSIVE = "**"