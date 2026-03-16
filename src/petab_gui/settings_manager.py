"""SettingsManager - Backward compatibility layer for application settings.

This module maintains backward compatibility by providing a singleton instance
of SettingsModel and re-exporting UI classes from the settings package.

For new code, prefer importing directly from the settings package:
    from petab_gui.settings import SettingsModel, SettingsDialog

This module is kept for backward compatibility with existing imports:
    from petab_gui.settings_manager import settings_manager, SettingsDialog
"""

from .settings import (
    ColumnConfigWidget,
    SettingsDialog,
    SettingsModel,
    TableDefaultsWidget,
)

# Create a single instance of the SettingsModel to be imported and used
settings_manager = SettingsModel()

# Re-export classes for backward compatibility
__all__ = [
    "settings_manager",
    "SettingsModel",
    "SettingsDialog",
    "ColumnConfigWidget",
    "TableDefaultsWidget",
]
