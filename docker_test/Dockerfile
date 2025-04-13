FROM homeassistant/home-assistant:latest

# Set environment variables
ENV PYTHONIOENCODING=UTF-8
ENV HASS_CONFIG_PATH=/config

# Install required packages for build
RUN apk add --no-cache git curl wget jq python3 python3-dev build-base libc6-compat libffi-dev openssl-dev cargo

# Make config directory
WORKDIR ${HASS_CONFIG_PATH}

# Install HACS
RUN mkdir -p /tmp/hacs && \
    curl -L -o /tmp/hacs.zip https://github.com/hacs/integration/releases/latest/download/hacs.zip && \
    mkdir -p /config/custom_components/hacs && \
    unzip -d /config/custom_components/hacs /tmp/hacs.zip && \
    rm -rf /tmp/hacs.zip

# Copy configuration.yaml for Home Assistant setup
COPY configuration.yaml /config/configuration.yaml

# Create directories for media files
RUN mkdir -p /config/media/2023-01-winter_photos && \
    mkdir -p /config/media/2024-06-summer_vacation && \
    mkdir -p /config/media/family_photos

# Download sample images from Pexels (more reliable than Unsplash)
RUN mkdir -p /tmp/sample_images && \
    cd /tmp/sample_images && \
    wget https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg -O winter1.jpg && \
    wget https://images.pexels.com/photos/730256/pexels-photo-730256.jpeg -O winter2.jpg && \
    wget https://images.pexels.com/photos/760971/pexels-photo-760971.jpeg -O winter3.jpg && \
    wget https://images.pexels.com/photos/1486974/pexels-photo-1486974.jpeg -O summer1.jpg && \
    wget https://images.pexels.com/photos/1450360/pexels-photo-1450360.jpeg -O summer2.jpg && \
    wget https://images.pexels.com/photos/1031628/pexels-photo-1031628.jpeg -O summer3.jpg && \
    wget https://images.pexels.com/photos/3883541/pexels-photo-3883541.jpeg -O family1.jpg && \
    wget https://images.pexels.com/photos/1128318/pexels-photo-1128318.jpeg -O family2.jpg && \
    wget https://images.pexels.com/photos/3807865/pexels-photo-3807865.jpeg -O family3.jpg && \
    cp winter*.jpg /config/media/2023-01-winter_photos/ && \
    cp summer*.jpg /config/media/2024-06-summer_vacation/ && \
    cp family*.jpg /config/media/family_photos/ && \
    rm -rf /tmp/sample_images

# Sample video files for testing (using reliable sources)
RUN mkdir -p /tmp/sample_videos && \
    cd /tmp/sample_videos && \
    wget https://filesamples.com/samples/video/mp4/sample_640x360.mp4 -O sample_video1.mp4 && \
    cp sample_video*.mp4 /config/media/family_photos/ && \
    rm -rf /tmp/sample_videos

# Create a setup script to run at container startup
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh

# Set the entry point to run the setup script and then start Home Assistant
ENTRYPOINT ["/setup.sh"]