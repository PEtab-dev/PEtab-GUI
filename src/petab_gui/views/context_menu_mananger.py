from PySide6.QtWidgets import QMenu


class ContextMenuManager:
    """Manage context menu actions for the tables."""

    def __init__(self, actions, table_view, parent=None):
        self.parent = parent()
        self.actions = actions
        self.table_view = table_view

    def create_context_menu(self, position):
        """Create the context menu."""
        menu = QMenu(self.parent)
        # Copy, Paste
        menu.addAction(self.actions["copy"])
        menu.addAction(self.actions["paste"])
        menu.addSeparator()
        menu.addAction(self.actions["add_row"])
        menu.addAction(self.actions["delete_row"])
        menu.addAction(self.actions["add_column"])
        menu.addAction(self.actions["delete_column"])
        menu.addSeparator()

        # execute the menu
        menu.exec_(self.table_view.viewport().mapToGlobal(position))
