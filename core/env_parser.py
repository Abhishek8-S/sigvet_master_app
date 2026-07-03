import os
from core.config_loader import get_config

def get_device_id(path=None):
    if path is None:
        path = get_config().get('paths', {}).get('env_path', "/opt/sigtuple/.pri.env")
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    if line.startswith("DEVICE_ID="):
                        return line.strip().split("=")[1]
    except Exception:
        pass
    return "UNKNOWN_DEVICE"
