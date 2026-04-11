from __future__ import annotations

from typing import ClassVar

from games.shared.input_manager_base import InputManagerBase
from games.shared.input_profiles import FPS_INPUT_PROFILES


class InputManager(InputManagerBase):
    """Manages input bindings and state for Force Field."""

    DEFAULT_BINDINGS: ClassVar[dict[str, int]] = {
        **FPS_INPUT_PROFILES["force_field"],
    }
