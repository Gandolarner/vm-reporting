from pathlib import Path

import yaml


THRESHOLD_FILE = Path("app/config/thresholds.yaml")

def load_thresholds() -> dict:
    """
    Load threshold configuration from YAML file.
    """

    with open(THRESHOLD_FILE, "r", encoding="utf-8") as file:
        thresholds = yaml.safe_load(file)

    return thresholds