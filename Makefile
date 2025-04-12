# Makefile for Picture Frame Controller development environment

# Configuration variables
PROJECT_DIR := $(shell pwd)
COMPONENT_NAME := picture_frame_controller
HA_CORE_DIR := $(PROJECT_DIR)/home-assistant-core
COMPONENT_DIR := $(PROJECT_DIR)/custom_components/$(COMPONENT_NAME)
TEST_DATA_DIR := /tmp/picture_frame_test
HA_CONFIG_DIR := $(HA_CORE_DIR)/config
DEVCONTAINER_FILE := $(HA_CORE_DIR)/.devcontainer/devcontainer.json

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

.PHONY: all setup clean config test-data vs-code help setup-mounts

all: setup

# Main setup target
setup: ha-core config test-data setup-mounts
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(GREEN)----------------------------------------------$(NC)"
	@echo "To use the development environment:"
	@echo "1. Open VS Code in the Home Assistant core directory:"
	@echo "   $(YELLOW)code $(HA_CORE_DIR)$(NC)"
	@echo "2. Run VS Code command: 'Dev Containers: Reopen in Container'"
	@echo ""
	@echo "Inside the container, you can:"
	@echo "- Validate your component:"
	@echo "   $(YELLOW)python -m script.hassfest validate$(NC)"
	@echo ""
	@echo "- Run your component's tests:"
	@echo "   $(YELLOW)python -m pytest custom_components/$(COMPONENT_NAME)/tests/$(NC)"
	@echo ""
	@echo "- Start a test instance of Home Assistant:"
	@echo "   $(YELLOW)hass -c ./config$(NC)"
	@echo "$(GREEN)----------------------------------------------$(NC)"

# Clone or update Home Assistant core
ha-core:
	@echo "$(GREEN)Setting up Home Assistant core repository...$(NC)"
	@if [ ! -d "$(HA_CORE_DIR)" ]; then \
		echo "$(GREEN)Cloning Home Assistant core repository...$(NC)"; \
		git clone https://github.com/home-assistant/core.git "$(HA_CORE_DIR)"; \
	else \
		echo "$(YELLOW)Home Assistant core repository already exists, updating...$(NC)"; \
		cd "$(HA_CORE_DIR)" && git pull; \
	fi
	@mkdir -p "$(HA_CORE_DIR)/custom_components"

# Set up Home Assistant configuration
config: ha-core
	@echo "$(GREEN)Setting up Home Assistant configuration...$(NC)"
	@mkdir -p "$(HA_CONFIG_DIR)"
	@if [ ! -f "$(HA_CONFIG_DIR)/configuration.yaml" ]; then \
		echo "# Minimal Home Assistant configuration for testing" > "$(HA_CONFIG_DIR)/configuration.yaml"; \
		echo "default_config:" >> "$(HA_CONFIG_DIR)/configuration.yaml"; \
		echo "" >> "$(HA_CONFIG_DIR)/configuration.yaml"; \
		echo "picture_frame_controller:" >> "$(HA_CONFIG_DIR)/configuration.yaml"; \
		echo "  media_paths:" >> "$(HA_CONFIG_DIR)/configuration.yaml"; \
		echo "    - \"/tmp/picture_frame_test/**\"" >> "$(HA_CONFIG_DIR)/configuration.yaml"; \
	fi

# Create test data directories and sample files
test-data:
	@echo "$(GREEN)Setting up test data directories...$(NC)"
	@mkdir -p "$(TEST_DATA_DIR)/2023-01-winter_photos"
	@mkdir -p "$(TEST_DATA_DIR)/2023-06-summer_vacation"
	@mkdir -p "$(TEST_DATA_DIR)/family_photos"
	@for dir in "$(TEST_DATA_DIR)/2023-01-winter_photos" "$(TEST_DATA_DIR)/2023-06-summer_vacation" "$(TEST_DATA_DIR)/family_photos"; do \
		for i in 1 2 3 4 5; do \
			touch "$$dir/test_image_$$i.jpg"; \
		done; \
	done

# Setup mounts by directly modifying devcontainer.json
setup-mounts: ha-core
	@echo "$(GREEN)Setting up mounts in devcontainer.json...$(NC)"
	@if grep -q "\"mounts\":" "$(DEVCONTAINER_FILE)"; then \
		echo "$(YELLOW)Mounts section already exists, updating...$(NC)"; \
		# For simplicity, we'll remove and re-add the mounts section to avoid complex sed replacements \
		sed -i '/^  "mounts": \[/,/^  \],/d' "$(DEVCONTAINER_FILE)"; \
	fi
	@# Insert the mounts section after runArgs section
	@sed -i '/^  "runArgs": \[/,/^  \],/s/^  \],/  \],\n  "mounts": [\n    "source=$(COMPONENT_DIR),target=\/workspaces\/home-assistant-core\/custom_components\/$(COMPONENT_NAME),type=bind,consistency=cached",\n    "source=$(TEST_DATA_DIR),target=\/tmp\/picture_frame_test,type=bind,consistency=cached",\n    "source=$(HA_CONFIG_DIR),target=\/workspaces\/home-assistant-core\/config,type=bind,consistency=cached"\n  ],/' "$(DEVCONTAINER_FILE)"
	@echo "$(GREEN)Mounts configured in $(DEVCONTAINER_FILE)$(NC)"

# VS Code task - optional helper
vs-code: ha-core
	@echo "$(GREEN)Opening VS Code in Home Assistant core directory...$(NC)"
	@code "$(HA_CORE_DIR)"

# Clean up everything
clean:
	@echo "$(RED)Removing Home Assistant core repository...$(NC)"
	@rm -rf "$(HA_CORE_DIR)"
	@echo "$(RED)Removing test data directory...$(NC)"
	@rm -rf "$(TEST_DATA_DIR)"
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Help target
help:
	@echo "Picture Frame Controller Development Environment"
	@echo "----------------------------------------------"
	@echo "Available targets:"
	@echo "  $(CYAN)setup$(NC)         - Set up the complete development environment"
	@echo "  $(CYAN)ha-core$(NC)       - Clone or update Home Assistant core repository"
	@echo "  $(CYAN)config$(NC)        - Create Home Assistant configuration for testing"
	@echo "  $(CYAN)test-data$(NC)     - Create test data directories and files"
	@echo "  $(CYAN)setup-mounts$(NC)  - Configure volume mounts in devcontainer.json"
	@echo "  $(CYAN)vs-code$(NC)       - Open VS Code in the Home Assistant core directory"
	@echo "  $(CYAN)clean$(NC)         - Remove all generated files and directories"
	@echo "  $(CYAN)help$(NC)          - Display this help message"