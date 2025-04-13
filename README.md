# Picture Frame Controller for Home Assistant

A Home Assistant custom component for controlling digital picture frames by managing image and video display from your media collection.

## Features

- **Media Discovery**: Automatically scan directories to find albums and media files
- **Intelligent Navigation**: Track viewed media to show unseen content
- **Filtering Capabilities**: Filter by album or date range
- **Interactive UI**: Custom Lovelace card for user interaction
- **Video Support**: Handles both images and video files
- **Previous Image**: Navigate back to previously shown images

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Custom repositories"
3. Add the repository URL: `https://github.com/yourusername/picture-frame-controller`
4. Select "Integration" as the category
5. Click "ADD"
6. Search for "Picture Frame Controller" and install

### Manual Installation

1. Download the `picture_frame_controller` directory from this repository
2. Copy it to the `custom_components` directory in your Home Assistant configuration
3. Restart Home Assistant

## Configuration

### Via the UI

1. Go to **Configuration** → **Integrations**
2. Click the "+" button to add a new integration
3. Search for "Picture Frame Controller"
4. Follow the configuration steps:
   - Add media directories to scan
   - Configure optional exclusion patterns
   - Set update interval and file types

### Configuration Options

- **Media Paths**: Directories to scan for media files
  - Use `/**` suffix for recursive scanning (e.g., `/photos/**`)
  - Use `/*` suffix for single-level scanning (e.g., `/photos/*`)
- **Exclude Patterns**: Regex patterns for directories to exclude
- **Update Interval**: How frequently to update the displayed image (seconds)
- **Image Extensions**: Supported image file extensions
- **Video Extensions**: Supported video file extensions

## Using the Component

### Services

The component provides the following services:

- `picture_frame_controller.next_image`: Show the next random unseen image
- `picture_frame_controller.previous_image`: Show the previously shown image
- `picture_frame_controller.set_album_filter`: Filter by album
  - Parameters: `album_name` (string)
- `picture_frame_controller.clear_album_filter`: Clear album filter
- `picture_frame_controller.set_time_range`: Filter by date range
  - Parameters: `start_year`, `start_month`, `end_year`, `end_month` (integers)
- `picture_frame_controller.clear_time_range`: Clear date range filter
- `picture_frame_controller.reset_seen_status`: Reset seen status for all media
- `picture_frame_controller.scan_media`: Re-scan media directories

### Lovelace Card

To add the picture frame controller card to your dashboard:

1. Edit your dashboard
2. Click "+ ADD CARD"
3. Scroll to the bottom and select "Custom: Picture Frame Card"
4. Configure the card:
   ```yaml
   type: custom:picture-frame-card
   entity: sensor.selected_image
   ```

## Album Organization

For best results, organize your albums with a date-based naming structure:

- Format: `YYYY-MM-AlbumName` or `YYYY_MM_AlbumName`
- Examples:
  - `2023-12-Christmas`
  - `2020_06_Vacation`

This allows the component to extract date information for time-based filtering.

## Sensors

The component creates the following sensors:

- `sensor.selected_image`: The current image being displayed
- `sensor.total_images`: Total count of media files
- `sensor.unseen_images`: Count of unseen media files

## Automation Examples

### Auto-start image display on Home Assistant startup

```yaml
automation:
  - alias: "Start Picture Frame on Startup"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: picture_frame_controller.next_image
```

### Create a scheduled display

```yaml
automation:
  - alias: "Show Pictures in the Evening"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: picture_frame_controller.set_time_range
        data:
          start_year: 2020
          start_month: 1
          end_year: 2023
          end_month: 12
      - service: picture_frame_controller.next_image
```

## Troubleshooting

- **No images found**: Ensure your media paths are correct and readable by Home Assistant
- **Incorrect album dates**: Verify your folder naming follows the YYYY-MM-Name format
- **Card not displaying**: Check that the custom card is correctly loaded

## Development / Contributing

Mostly written by Claude 3.7 Sonet as Agent Chat in VS Code CoPilot in agentic mode. High-level (vibe-coding) guidance by author. Manual commits should be prefixed with MAN (or similar, was not very consistent).

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.