"""Configuration utils to load config from yaml/json."""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import yaml


class MLOpsConfig:
    """MLopsConfig Class."""

    _raw_config: Any

    def __init__(
        self, environment: str = "pr", config_path: Path = "config/config.yaml"
    ):
        """Intialize MLConfig with yaml config data."""
        self.config_path = config_path
        self._environment = environment
        load_dotenv()
        with open(config_path, "r", encoding="utf-8") as stream:
            self._raw_config = yaml.safe_load(os.path.expandvars(stream.read()))

    def __getattr__(self, __name: str) -> Any:
        """Get values for top level keys in configuration."""
        return self._raw_config[__name]

    def get_flow_config(self, flow_name: str) -> Dict:
        """Get the pipeline configuration for given flow name and environment."""
        flowconfig_name = f"{flow_name}_{self._environment}"
        if flowconfig_name in self._raw_config:
            return self._raw_config[flowconfig_name]


if __name__ == "__main__":
    mlconfig = MLOpsConfig()
