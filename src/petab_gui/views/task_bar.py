from PySide6.QtWidgets import QMenu, QStyle
from PySide6.QtGui import QAction


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
        return "File"
    def __init__(self, parent, actions):
        super().__init__(parent, actions)

        # Open, Save, and Close actions
        self.upload_yaml_action = actions["open_yaml"]
        self.menu.addAction(self.upload_yaml_action)
        self.save_action = actions["save"]
        self.menu.addAction(self.save_action)


class EditMenu(BasicMenu):
    # TODO: Add actions to the setup actions (Requires fix of those, will be
    #  done in the next PR)
    """Edit Menu of the TaskBar."""
    def menu_name(self):
        return "Edit"

    def __init__(self, parent, actions):
        super().__init__(parent, actions)

        # Find and Replace
        self.find_replace_action = self.add_action_or_menu("Find/Replace")
        # Add Columns submenu
        self.add_column_menu = self.add_action_or_menu(
            "Add Column to ...", is_action=False
        )
        self.add_c_meas_action = self.add_action_or_menu(
            "... Measurement Table", self.add_column_menu
        )
        self.add_c_obs_action = self.add_action_or_menu(
            "... Observable Table", self.add_column_menu
        )
        self.add_c_para_action = self.add_action_or_menu(
            "... Parameter Table", self.add_column_menu
        )
        self.add_c_cond_action = self.add_action_or_menu(
            "... Condition Table", self.add_column_menu
        )
        # Add Rows submenu
        self.menu.addAction(actions["add_row"])
        self.menu.addAction(actions["delete_row"])


class ViewMenu(BasicMenu):
    """View Menu of the TaskBar."""
    def menu_name(self):
        return "View"

    def __init__(self, parent, actions):
        super().__init__(parent, actions)

        # Add actions to the menu for re-adding tables
        self.menu.addAction(actions["show_measurement"])
        self.menu.addAction(actions["show_observable"])
        self.menu.addAction(actions["show_parameter"])
        self.menu.addAction(actions["show_condition"])
        self.menu.addAction(actions["show_logger"])
        self.menu.addAction(actions["show_plot"])


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
