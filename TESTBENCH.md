# Picture Frame Controller Testbench

This document outlines procedures for testing the Picture Frame Controller component for Home Assistant.

## Development Environment Setup

### Requirements

- Python 3.9+
- Home Assistant development environment
- Docker (optional, for containerized testing)

### Setting Up the Dev Container

1. **Using VS Code**:
   - Open the project in VS Code
   - When prompted, click "Reopen in Container"
   - VS Code will build and start the development container

2. **Manual Dev Container Setup**:
   ```bash
   docker-compose -f .devcontainer/docker-compose.yml up -d
   ```

### Installing Development Dependencies

```bash
pip install -r requirements_dev.txt
```

## Running Tests

### Unit Tests

Run the full test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=custom_components.picture_frame_controller
```

Run specific test files:

```bash
pytest tests/test_init.py
pytest tests/test_media_scanner.py
pytest tests/test_database_manager.py
pytest tests/test_config_flow.py
```

### Integration Tests

For running integration tests with a full Home Assistant instance:

```bash
pytest tests/integration
```

## Manual Testing Procedures

### Test Data Setup

1. Create a test directory structure:
   ```bash
   mkdir -p /tmp/picture_frame_test/2023-01-winter_photos
   mkdir -p /tmp/picture_frame_test/2023-06-summer_vacation
   mkdir -p /tmp/picture_frame_test/family_photos
   
   # Add some test images
   cp test_images/* /tmp/picture_frame_test/2023-01-winter_photos/
   cp test_images/* /tmp/picture_frame_test/2023-06-summer_vacation/
   cp test_images/* /tmp/picture_frame_test/family_photos/
   ```

### Component Installation Testing

1. Build the component:
   ```bash
   cd /home/schirner/project/pic-fram-control-2
   zip -r picture_frame_controller.zip custom_components/picture_frame_controller
   ```

2. Install in a test Home Assistant instance:
   - Copy the zip file to your Home Assistant configuration directory
   - Unzip it into the `custom_components` directory
   - Restart Home Assistant

### UI Testing Checklist

1. **Configuration Flow**:
   - [ ] Component appears in integration list
   - [ ] Configuration form displays correctly
   - [ ] Path validation works
   - [ ] Configuration is saved properly

2. **Sensor Testing**:
   - [ ] All sensors appear after setup
   - [ ] Selected image shows correct path
   - [ ] Count sensors show accurate numbers
   - [ ] Attributes contain expected information

3. **Card Testing**:
   - [ ] Card loads correctly in dashboard
   - [ ] Images display properly
   - [ ] Videos play correctly
   - [ ] Next/Previous buttons work
   - [ ] Album filter functions
   - [ ] Time range filter functions

4. **Service Testing**:
   - [ ] Next image service changes the image
   - [ ] Previous image service works
   - [ ] Album filtering limits images correctly
   - [ ] Time range filtering limits images correctly
   - [ ] Reset seen status resets all media
   - [ ] Scan media service finds new files

## Database Testing

### Database Integrity

Check database integrity:

```bash
cd ~/.homeassistant
sqlite3 picture_frame_controller.db "PRAGMA integrity_check;"
```

### Database Schema Validation

```bash
sqlite3 ~/.homeassistant/picture_frame_controller.db ".schema"
```

Expected output should match the schema definitions in the design document.

### Query Testing

Check media counts:

```bash
sqlite3 ~/.homeassistant/picture_frame_controller.db "SELECT COUNT(*) FROM albums;"
sqlite3 ~/.homeassistant/picture_frame_controller.db "SELECT COUNT(*) FROM media_files;"
```

Check seen status:

```bash
sqlite3 ~/.homeassistant/picture_frame_controller.db "SELECT COUNT(*) FROM media_files WHERE seen = 1;"
```

## Performance Testing

### Media Scan Performance

Test with a large dataset:
1. Create test data with many files (500+ images)
2. Time the initial scan
3. Monitor memory usage during scan

### Response Time Testing

Measure time to:
- Initial load
- Next image service call
- Previous image service call
- Filter application

## Stress Testing

Run the component with:
- Many media files (1000+)
- Frequent service calls (every few seconds)
- Multiple concurrent users accessing the dashboard

## Compatibility Testing

Test on multiple Home Assistant versions:
- Current stable release
- Latest development version
- Previous stable release

## Bug Reporting

When submitting a bug report, please include:

1. Component version
2. Home Assistant version
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Screenshots if applicable
7. Logs from Home Assistant

## Release Checklist

Before releasing a new version:

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Version numbers are updated
- [ ] CHANGELOG.md is updated
- [ ] Component validates with Home Assistant hassfest
- [ ] Custom card builds successfully