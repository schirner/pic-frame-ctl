#!/bin/sh

# Create necessary directories if they don't exist
mkdir -p /config/themes
mkdir -p /config/dashboards
mkdir -p /config/www/community
mkdir -p /config/.storage

# Create album directories following the YYYY-MM-AlbumName convention
mkdir -p /config/media/2022-01-Winter
mkdir -p /config/media/2022-06-Summer
mkdir -p /config/media/2023-04-Spring
mkdir -p /config/media/2023-09-Fall
mkdir -p /config/media/2024-12-Holiday
mkdir -p /config/media/2023-10-FamilyTrips/Beach
mkdir -p /config/media/2023-10-FamilyTrips/Mountains
mkdir -p /config/media/2024-03-Vacations/Europe
mkdir -p /config/media/2024-03-Vacations/Asia

# Create a basic theme file if none exists
if [ ! -f /config/themes.yaml ]; then
  echo "# Default themes" > /config/themes.yaml
fi



# Run the test image generator
echo "Generating test images for Picture Frame Controller..."
mkdir -p /config/media/test_generated_media
cd /config/scripts
python3 generate_test_images.py --count 10

# Create dashboard for picture frame
cat > /config/dashboards/picture_frame.yaml << 'EOF'
title: Picture Frame Dashboard
views:
  - title: Main
    path: main
    icon: mdi:image
    cards:
      - type: entities
        title: Picture Frame Controller Status
        entities:
          - entity: sensor.picture_frame_controller_selected_image
          - entity: sensor.picture_frame_controller_total_images
          - entity: sensor.picture_frame_controller_unseen_images
      
      - type: picture-entity
        entity: sensor.picture_frame_controller_selected_image
        camera_view: auto
        show_state: false
        show_name: false
      
      - type: entities
        title: Picture Frame Services
        show_header_toggle: false
        entities:
          - type: button
            name: Next Image
            tap_action:
              action: call-service
              service: picture_frame_controller.next_image
          - type: button
            name: Previous Image
            tap_action:
              action: call-service
              service: picture_frame_controller.previous_image
          - type: button
            name: Reset Seen Status
            tap_action:
              action: call-service
              service: picture_frame_controller.reset_seen_status
          - type: button
            name: Scan Media
            tap_action:
              action: call-service
              service: picture_frame_controller.scan_media
EOF


# Start Home Assistant
echo "Starting Home Assistant..."
exec hass