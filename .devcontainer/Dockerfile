FROM homeassistant/home-assistant:latest

# Additional dependencies for development and testing
RUN apk add --no-cache \
    git \
    python3-dev \
    build-base \
    && pip3 install --no-cache-dir pytest pytest-cov pytest-homeassistant-custom-component pre-commit black flake8

# Set work directory
WORKDIR /config

# Create the custom_components directory symlink
RUN mkdir -p /config/custom_components