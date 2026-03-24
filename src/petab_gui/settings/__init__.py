"""Settings package for PEtab GUI.

This package contains the settings management system, split into:
- SettingsModel: Pure data/persistence layer (no UI dependencies)
- SettingsDialog: Pure UI layer for the settings dialog
"""

from .settings_dialog import (
    ColumnConfigWidget,
    SettingsDialog,
    TableDefaultsWidget,
)
from .settings_model import SettingsModel

__all__ = [
    "SettingsModel",
    "SettingsDialog",
    "ColumnConfigWidget",
    "TableDefaultsWidget",
]
