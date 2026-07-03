import yaml
import os

_CONFIG_CACHE = None

def get_config():
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            _CONFIG_CACHE = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config.yaml: {e}")
        _CONFIG_CACHE = {}
        
    return _CONFIG_CACHE
