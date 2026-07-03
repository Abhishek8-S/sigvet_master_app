import json
import os
import yaml

# Resolve paths relative to this file's location (core/ → parent = install root).
# This ensures config files are found regardless of the current working directory,
# which is critical when the app is launched as root via sudo from a .desktop entry.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_settings():
    """Loads general UI settings."""
    path = os.path.join(_BASE_DIR, 'config', 'settings.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_benchmarks():
    """Loads expected values for tests."""
    path = os.path.join(_BASE_DIR, 'config', 'benchmark_values.yaml')
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def load_device_profiles():
    """Loads device-specific overrides."""
    path = os.path.join(_BASE_DIR, 'config', 'device_profiles.yaml')
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