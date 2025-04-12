#!/usr/bin/env python3
"""
Configure the VS Code devcontainer.json file with proper mount points for development.

This script modifies the devcontainer.json file to add mount points for:
1. The custom component directory
2. The test data directory
3. The Home Assistant configuration directory
4. The tests directory
"""

import json
import os
import sys
import re


def strip_comments(json_string):
    """
    Strip comments from a JSON string.
    Comments can be // ... or /* ... */
    """
    # First, handle // comments
    pattern = r'//.*?(?=\n|$)'
    json_string = re.sub(pattern, '', json_string)
    
    # Then handle /* ... */ comments
    pattern = r'/\*.*?\*/'
    json_string = re.sub(pattern, '', json_string, flags=re.DOTALL)
    
    return json_string


def configure_devcontainer_mounts(devcontainer_file, component_dir, 
                                  component_name, test_data_dir, config_dir):
    """
    Configure the VS Code devcontainer.json file with proper mount points.
    
    Args:
        devcontainer_file: Path to the devcontainer.json file
        component_dir: Path to the component directory
        component_name: Name of the component
        test_data_dir: Path to the test data directory
        config_dir: Path to the Home Assistant configuration directory
    """
    print(f"Configuring mounts in {devcontainer_file}")
    
    try:
        # Read the file as text first
        with open(devcontainer_file, 'r') as f:
            json_text = f.read()
        
        # Strip comments
        json_text = strip_comments(json_text)
        
        # Parse as JSON
        data = json.loads(json_text)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    # Get the project root directory (parent of component_dir)
    project_root = os.path.dirname(os.path.dirname(component_dir))
    tests_dir = os.path.join(project_root, "tests")
    
    # Define the mounts
    mounts = [
        f"source={component_dir},target=/workspaces/home-assistant-core/custom_components/{component_name},type=bind,consistency=cached",
        f"source={test_data_dir},target=/tmp/picture_frame_test,type=bind,consistency=cached",
        f"source={config_dir},target=/workspaces/home-assistant-core/config,type=bind,consistency=cached",
        f"source={tests_dir},target=/workspaces/home-assistant-core/tests/components/{component_name},type=bind,consistency=cached"
    ]
    
    # Update the mounts in the JSON data
    data["mounts"] = mounts
    
    # Write back to the file - making sure we preserve the original structure
    with open(devcontainer_file, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=False)
    
    print(f"Successfully configured mounts in {devcontainer_file}")


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: configure_devcontainer.py <devcontainer_file> <component_dir> "
              "<component_name> <test_data_dir> <config_dir>")
        sys.exit(1)
        
    devcontainer_file = sys.argv[1]
    component_dir = sys.argv[2]
    component_name = sys.argv[3]
    test_data_dir = sys.argv[4]
    config_dir = sys.argv[5]
    
    configure_devcontainer_mounts(devcontainer_file, component_dir, 
                                 component_name, test_data_dir, config_dir)