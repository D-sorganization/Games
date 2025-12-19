"""Configuration management for Force Field game."""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GameConfig:
    """Manages game configuration from environment variables and defaults."""

    def __init__(self) -> None:
        """Initialize configuration with defaults and environment overrides."""
        self._config: dict[str, Any] = {}
        self._load_defaults()
        self._load_from_environment()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config.update(
            {
                # Game Settings
                "debug": False,
                "log_level": "INFO",
                "fullscreen": False,
                # Performance Settings
                "render_scale": 4,
                "target_fps": 60,
                "max_bots": 50,
                # Audio Settings
                "master_volume": 0.7,
                "music_volume": 0.5,
                "sfx_volume": 0.8,
                "enable_audio": True,
                # Graphics Settings
                "screen_width": 1200,
                "screen_height": 800,
                "vsync": True,
                "show_fps": False,
                # Gameplay Settings
                "default_difficulty": "NORMAL",
                "default_lives": 3,
                "default_map_size": 40,
                "enable_cheats": False,
                "show_debug_info": False,
                # Controls
                "mouse_sensitivity": 1.0,
                "invert_mouse": False,
            }
        )

    def _load_from_environment(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mappings = {
            "FORCE_FIELD_DEBUG": ("debug", self._parse_bool),
            "FORCE_FIELD_LOG_LEVEL": ("log_level", str),
            "FORCE_FIELD_FULLSCREEN": ("fullscreen", self._parse_bool),
            "FORCE_FIELD_RENDER_SCALE": ("render_scale", int),
            "FORCE_FIELD_TARGET_FPS": ("target_fps", int),
            "FORCE_FIELD_MASTER_VOLUME": ("master_volume", float),
            "FORCE_FIELD_MUSIC_VOLUME": ("music_volume", float),
            "FORCE_FIELD_SFX_VOLUME": ("sfx_volume", float),
            "FORCE_FIELD_ENABLE_CHEATS": ("enable_cheats", self._parse_bool),
            "FORCE_FIELD_SHOW_DEBUG_INFO": ("show_debug_info", self._parse_bool),
            "FORCE_FIELD_MOUSE_SENSITIVITY": ("mouse_sensitivity", float),
        }

        for env_var, (config_key, parser) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    self._config[config_key] = parser(env_value)
                    logger.debug(
                        "Loaded %s = %s from environment", config_key, env_value
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        "Invalid value for %s: %s (%s)", env_var, env_value, e
                    )

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        return value.lower() in ("true", "1", "yes", "on")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()

    def save_to_file(self, filepath: Path | None = None) -> None:
        """Save current configuration to file."""
        if filepath is None:
            filepath = Path("force_field_config.txt")

        try:
            with open(filepath, "w") as f:
                f.write("# Force Field Game Configuration\n")
                f.write(
                    "# Generated automatically - modify environment variables "
                    "instead\n\n"
                )

                for key, value in sorted(self._config.items()):
                    f.write(f"{key} = {value}\n")

            logger.info("Configuration saved to %s", filepath)
        except OSError as e:
            logger.error("Failed to save configuration: %s", e)

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Validate numeric ranges
        if not (1 <= self.get("render_scale", 4) <= 8):
            issues.append("render_scale must be between 1 and 8")

        if not (30 <= self.get("target_fps", 60) <= 120):
            issues.append("target_fps must be between 30 and 120")

        if not (0.0 <= self.get("master_volume", 0.7) <= 1.0):
            issues.append("master_volume must be between 0.0 and 1.0")

        if not (0.1 <= self.get("mouse_sensitivity", 1.0) <= 5.0):
            issues.append("mouse_sensitivity must be between 0.1 and 5.0")

        # Validate screen dimensions
        width = self.get("screen_width", 1200)
        height = self.get("screen_height", 800)
        if width < 800 or height < 600:
            issues.append("Screen resolution must be at least 800x600")

        return issues

    def apply_logging_config(self) -> None:
        """Apply logging configuration."""
        log_level = self.get("log_level", "INFO").upper()

        try:
            numeric_level = getattr(logging, log_level)
            logging.getLogger().setLevel(numeric_level)
            logger.info("Log level set to %s", log_level)
        except AttributeError:
            logger.warning("Invalid log level: %s, using INFO", log_level)
            logging.getLogger().setLevel(logging.INFO)
