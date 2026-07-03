import json
import os
import yaml

def load_settings():
    """Loads general UI settings."""
    path = os.path.join('config', 'settings.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_benchmarks():
    """Loads expected values for tests."""
    path = os.path.join('config', 'benchmark_values.yaml')
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def load_device_profiles():
    """Loads device-specific overrides."""
    path = os.path.join('config', 'device_profiles.yaml')
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

CONFIG = load_settings()
# Initialize with defaults
BENCHMARK_STANDARDS = load_benchmarks()
DEVICE_PROFILES = load_device_profiles()

def apply_device_profile(profile_name):
    """Updates BENCHMARK_STANDARDS with values from a selected profile."""
    # Use the global variables loaded at module level
    profiles = DEVICE_PROFILES
    selected = profiles.get(profile_name, {})
    
    global BENCHMARK_STANDARDS
    
    # Deep merge logic: Update existing keys with new values
    for test_name, overrides in selected.items():
        if test_name in BENCHMARK_STANDARDS:
            BENCHMARK_STANDARDS[test_name].update(overrides)
        else:
            # If the test wasn't in the default yaml but is in the profile, add it
            BENCHMARK_STANDARDS[test_name] = overrides