"""Find and Replace Controller.

This controller mediates find/replace operations across multiple table
controllers. It owns the coordination logic for searching, highlighting,
and replacing across multiple tables.
"""


class FindReplaceController:
    """Coordinates find/replace operations across multiple table controllers.

    This controller provides a clean interface for the FindReplaceBar view to
    search, highlight, focus, and replace text across multiple tables without
    knowing about individual table controllers. It works as a mediator
    encapsulating the coordination logic between multiple table controllers.
    """

    def __init__(self, table_controllers: dict):
        """Initialize the find/replace controller.

        Args:
            table_controllers: Dictionary mapping table names to their
            controllers.
            Example: {"Measurement Table": measurement_controller, ...}
        """
        self.table_controllers = table_controllers

    def get_table_names(self) -> list[str]:
        """Get list of available table names.

        Returns:
            List of table names that can be searched.
        """
        return list(self.table_controllers.keys())

    def find_text(
        self,
        search_text: str,
        case_sensitive: bool,
        regex: bool,
        whole_cell: bool,
        selected_table_names: list[str],
    ) -> list[tuple]:
        """Search for text across selected tables.

        Args:
            search_text: The text to search for
            case_sensitive: Whether search is case-sensitive
            regex: Whether to use regex matching
            whole_cell: Whether to match whole cell only
            selected_table_names: List of table names to search in

        Returns:
            List of tuples: (row, col, table_name, controller)
            Each tuple represents a match with its location and associated
            controller.
        """
        matches = []

        for table_name in selected_table_names:
            controller = self.table_controllers.get(table_name)
            if controller is None:
                continue

            # Get matches from this table
            table_matches = controller.find_text(
                search_text, case_sensitive, regex, whole_cell
            )

            # Extend with table name and controller reference
            for row, col in table_matches:
                matches.append((row, col, table_name, controller))

        return matches

    def focus_match(
        self, table_name: str, row: int, col: int, with_focus: bool = False
    ):
        """Focus on a specific match in a table.

        Args:
            table_name: Name of the table containing the match
            row: Row index of the match
            col: Column index of the match
            with_focus: Whether to give the table widget focus
        """
        controller = self.table_controllers.get(table_name)
        if controller:
            controller.focus_match((row, col), with_focus=with_focus)

    def unfocus_match(self, table_name: str):
        """Remove focus from current match in a table.

        Args:
            table_name: Name of the table to unfocus
        """
        controller = self.table_controllers.get(table_name)
        if controller:
            controller.focus_match(None)

    def replace_text(
        self,
        table_name: str,
        row: int,
        col: int,
        replace_text: str,
        search_text: str,
        case_sensitive: bool,
        regex: bool,
    ):
        """Replace text in a specific cell.

        Args:
            table_name: Name of the table containing the cell
            row: Row index
            col: Column index
            replace_text: Text to replace with
            search_text: Original search text (for validation)
            case_sensitive: Whether the original search was case-sensitive
            regex: Whether the original search used regex
        """
        controller = self.table_controllers.get(table_name)
        if controller:
            controller.replace_text(
                row=row,
                col=col,
                replace_text=replace_text,
                search_text=search_text,
                case_sensitive=case_sensitive,
                regex=regex,
            )

    def replace_all(
        self,
        search_text: str,
        replace_text: str,
        case_sensitive: bool,
        regex: bool,
        matches: list[tuple],
    ):
        """Replace all matches across tables.

        Args:
            search_text: Text to search for
            replace_text: Text to replace with
            case_sensitive: Whether search is case-sensitive
            regex: Whether to use regex
            matches: List of match tuples from find_text()
        """
        # Group matches by controller
        controllers_to_update = {}
        for row, col, _, controller in matches:
            if controller not in controllers_to_update:
                controllers_to_update[controller] = []
            controllers_to_update[controller].append((row, col))

        # Call replace_all on each unique controller
        for controller, positions in controllers_to_update.items():
            controller.replace_all(
                search_text, replace_text, case_sensitive, regex
            )
            # Emit dataChanged for each affected cell
            for row, col in positions:
                controller.model.dataChanged.emit(
                    controller.model.index(row, col),
                    controller.model.index(row, col),
                )

    def cleanse_all_highlights(self):
        """Clear highlights from all tables."""
        for controller in self.table_controllers.values():
            controller.cleanse_highlighted_cells()

    def highlight_matches(self, matches: list[tuple]):
        """Highlight matches in their respective tables.

        Args:
            matches: List of match tuples from find_text()
        """
        # Group matches by controller
        by_controller = {}
        for row, col, _, controller in matches:
            if controller not in by_controller:
                by_controller[controller] = []
            by_controller[controller].append((row, col))

        # Highlight in each table
        for controller, positions in by_controller.items():
            controller.highlight_text(positions)
