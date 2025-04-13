FROM homeassistant/home-assistant:latest

# Set environment variables
ENV PYTHONIOENCODING=UTF-8
ENV HASS_CONFIG_PATH=/config

# Install required packages for build
RUN apk add --no-cache git curl wget jq python3 python3-dev build-base libc6-compat libffi-dev openssl-dev cargo py3-pip

# Install Pillow for image generation
RUN pip3 install pillow

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

# Create a scripts directory and copy the image generator script
RUN mkdir -p /config/scripts
COPY generate_test_images.py /config/scripts/
RUN chmod +x /config/scripts/generate_test_images.py

# Create a setup script to run at container startup
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh

# Set the entry point to run the setup script and then start Home Assistant
ENTRYPOINT ["/setup.sh"]