# Picture Frame Controller Development Environment

This document explains how to set up and use the development environment for the Picture Frame Controller Home Assistant integration.

## Overview

The development setup uses the Home Assistant development container with a Docker Compose override to mount your component files directly into the container. This approach ensures:

- Your component files are visible in the container without copying or symbolic links
- Test data is available in the container
- Custom configurations are properly mounted
- All changes are immediately visible in the development environment

## Quick Start

1. Set up the development environment:
   ```bash
   make setup
   ```

2. Open VS Code in the Home Assistant core directory:
   ```bash
   make vs-code
   ```

3. When prompted in VS Code, select "Reopen in Container"

4. Once inside the dev container, you can:
   - Validate your component:
     ```bash
     python -m script.hassfest validate
     ```
   - Run your component's tests:
     ```bash
     python -m pytest custom_components/picture_frame_controller/tests/
     ```
   - Start a test instance of Home Assistant:
     ```bash
     hass -c ./config
     ```

5. When done, clean up the environment:
   ```bash
   make clean
   ```

## How It Works

The setup creates:

1. **Docker Compose Override**: Configures volume mounts to make your code accessible inside the container
2. **Test Data**: Creates sample media files for testing
3. **Custom Configuration**: Sets up Home Assistant configuration for your component

### Volume Mounts

The Docker Compose override mounts these directories:

- **Component Files**: Your custom component files from `custom_components/picture_frame_controller` are mounted to `/workspaces/core/custom_components/picture_frame_controller`
- **Test Data**: Sample media files in `/tmp/picture_frame_test` are mounted to the same path in the container
- **Configuration**: Custom Home Assistant config is mounted to `/workspaces/core/config`

### Development Workflow

1. Make changes to your component files in your main project
2. The changes are immediately available in the dev container
3. Test and validate your changes inside the container

## Makefile Commands

- `make setup`: Set up the complete development environment
- `make clean`: Remove all generated files and directories
- `make test-data`: Create or refresh test data directories and files
- `make vs-code`: Open VS Code in the Home Assistant core directory
- `make help`: Display help information

## VS Code Tasks

Several VS Code tasks are configured to make development easier:

1. `Setup Development Environment`: Runs the complete setup
2. `Open Home Assistant Core in VS Code`: Opens VS Code in the HA core directory
3. `Clean Development Environment`: Cleans up all generated files
4. `Create Test Data`: Generates sample media files for testing

To run these tasks, press `Ctrl+Shift+P`, type "Tasks: Run Task", and select the desired task.