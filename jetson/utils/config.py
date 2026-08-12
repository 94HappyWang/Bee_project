import os
import json
import logging

logger = logging.getLogger("BeeConfig")

DEFAULT_CONFIG_PATH = os.path.join("data", "config.json")

DEFAULT_CONFIG = {
    "camera_source": "0",
    "model_path": "yolo26s.pt",
    "conf_threshold": 0.3,
    "iou_threshold": 0.45,
    "line_a": [100, 150, 540, 150],  # [x1, y1, x2, y2] Line A (Outdoor)
    "line_b": [100, 330, 540, 330],  # [x3, y3, x4, y4] Line B (Hive Entrance)
    "line_a_name": "Line A (室外端)",
    "line_b_name": "Line B (門口端)",
    "max_crossing_time": 5.0,        # Maximum seconds between crossing Line A and B
    "db_path": os.path.join("data", "bee_logs.sqlite"),
    "csv_path": os.path.join("data", "bee_logs.csv")
}


class ConfigManager:
    """System Configuration Manager handling local config.json load/save."""

    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Loads configuration from config.json."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    self.data.update(user_data)
                logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to read {self.config_path}: {e}, using defaults.")
        else:
            self.save()

    def save(self):
        """Saves current configuration to config.json."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, auto_save=True):
        self.data[key] = value
        if auto_save:
            self.save()

    def get_lines(self):
        """Returns tuple (line_a_coords, line_b_coords)."""
        return tuple(self.data.get("line_a")), tuple(self.data.get("line_b"))

    def set_lines(self, line_a, line_b, auto_save=True):
        """Sets Line A [x1, y1, x2, y2] and Line B [x3, y3, x4, y4]."""
        self.data["line_a"] = list(line_a)
        self.data["line_b"] = list(line_b)
        if auto_save:
            self.save()
