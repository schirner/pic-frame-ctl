#!/bin/sh

# Create necessary directories if they don't exist
mkdir -p /config/themes
mkdir -p /config/dashboards
mkdir -p /config/www/community
mkdir -p /config/.storage

# Create a basic theme file if none exists
if [ ! -f /config/themes.yaml ]; then
  echo "# Default themes" > /config/themes.yaml
fi

# Create GitHub token placeholder if it doesn't exist
if [ ! -f /config/secrets.yaml ]; then
  echo "# Replace with your actual GitHub token for HACS" > /config/secrets.yaml
  echo "github_token: xxx" >> /config/secrets.yaml
  echo "For full HACS functionality, you need to add your GitHub token to /config/secrets.yaml"
fi

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

# Link the Picture Frame Controller custom component
echo "Linking the Picture Frame Controller custom component..."
mkdir -p /config/custom_components
ln -s /picture_frame_controller /config/custom_components/picture_frame_controller

# Start Home Assistant
echo "Starting Home Assistant..."
exec hass