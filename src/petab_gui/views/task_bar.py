from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
import qtawesome as qta


class BasicMenu:
    """Base class for a TaskBar Menu."""
    def __init__(self, parent, actions):
        self.menu = QMenu(self.menu_name(), parent)
        self.parent = parent

    def add_action_or_menu(
        self, name: str, menu: QMenu = None, is_action: bool = True
    ):
        """Add an action or a menu to the menu.

        If no menu is provided, the action is added to the main menu."""
        if menu is None:
            menu = self.menu
        if is_action:
            action = QAction(name, self.parent)
            menu.addAction(action)
        else:
            action = QMenu(name, self.parent)
            menu.addMenu(action)
        return action

    def add_checkable_action(self, name: str, menu: QMenu = None):
        """Add a checkable action to the menu."""
        action = self.add_action_or_menu(name, menu)
        action.setCheckable(True)
        action.setChecked(True)
        return action

    def menu_name(self):
        """This method should be overridden to provide the menu's name."""
        raise NotImplementedError("Subclasses must provide a menu name.")


class FileMenu(BasicMenu):
    """Class for the file menu."""
    def menu_name(self):
        return "&File"

    def __init__(self, parent, actions):
        super().__init__(parent, actions)

        # Open, Save, and Close actions
        self.menu.addAction(actions["new"])
        self.menu.addAction(actions["open"])
        self.menu.addAction(actions["add"])
        self.menu.addAction(actions["save"])
        self.menu.addMenu(actions["recent_files"])
        self.menu.addSeparator()
        self.menu.addAction(actions["close"])


class EditMenu(BasicMenu):
    # TODO: Add actions to the setup actions (Requires fix of those, will be
    #  done in the next PR)
    """Edit Menu of the TaskBar."""
    def menu_name(self):
        return "&Edit"

    def __init__(self, parent, actions):
        super().__init__(parent, actions)

        # Find and Replace
        self.menu.addAction(actions["find"])
        self.menu.addAction(actions["find+replace"])
        self.menu.addSeparator()
        # Copy, Paste
        self.menu.addAction(actions["copy"])
        self.menu.addAction(actions["paste"])
        self.menu.addSeparator()
        # Add Columns
        self.menu.addAction(actions["add_column"])
        self.menu.addAction(actions["delete_column"])
        # Add Rows
        self.menu.addAction(actions["add_row"])
        self.menu.addAction(actions["delete_row"])
        self.menu.addSeparator()
        # Reset Model
        self.menu.addAction(actions["reset_model"])
        self.menu.addSeparator()
        # Settings
        self.menu.addAction(actions["settings"])
        self.menu.addSeparator()


class ViewMenu(BasicMenu):
    """View Menu of the TaskBar."""
    def menu_name(self):
        return "&View"

    def __init__(self, parent, actions):
        super().__init__(parent, actions)

        # Add actions to the menu for re-adding tables
        visibility_header = QAction(
            qta.icon("fa5s.eye"), "Visibility", parent
        )
        visibility_header.setEnabled(False)
        self.menu.addAction(visibility_header)
        self.menu.addSeparator()
        self.menu.addAction(actions["show_measurement"])
        self.menu.addAction(actions["show_observable"])
        self.menu.addAction(actions["show_parameter"])
        self.menu.addAction(actions["show_condition"])
        self.menu.addAction(actions["show_logger"])
        self.menu.addAction(actions["show_plot"])
        self.menu.addSeparator()
        self.menu.addAction(actions["clear_log"])


class TaskBar:
    """TaskBar of the PEtab Editor."""
    def add_menu(self, menu_class, actions):
        """Add a menu to the task bar."""
        menu = menu_class(self.parent, actions)
        self.menu.addMenu(menu.menu)
        return menu

    def __init__(self, parent, actions):
        self.parent = parent
        self.menu = parent.menuBar()
        self.file_menu = self.add_menu(FileMenu, actions)
        self.edit_menu = self.add_menu(EditMenu, actions)
        self.view_menu = self.add_menu(ViewMenu, actions)
