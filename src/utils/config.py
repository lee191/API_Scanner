"""Configuration loader and manager."""

import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration."""
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value

    @property
    def proxy_host(self) -> str:
        """Get proxy host."""
        return self.get('proxy.host', '127.0.0.1')

    @property
    def proxy_port(self) -> int:
        """Get proxy port."""
        return self.get('proxy.port', 8080)

    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self.get('output.directory', 'output')

    @property
    def scanner_checks(self) -> list:
        """Get scanner checks."""
        return self.get('scanner.checks', [])


# Global config instance
_config: Config = None


def get_config(config_path: str = "config/config.yaml") -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
