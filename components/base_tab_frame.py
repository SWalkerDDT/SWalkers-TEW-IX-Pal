import tkinter as tk

class BaseTabFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db_connection = None

    def set_db_connection(self, db):
        """
        Set the database connection for this tab.
        Args:
            db: The database connection object.
        """
        self.db_connection = db

    def go_to_tab(self, tab_name):
        """
        Switch to the tab with the given name (case-insensitive, matches tab text).
        """
        notebook = self.controller.notebook
        for idx in range(notebook.index('end')):
            if notebook.tab(idx, 'text').lower() == tab_name.lower():
                notebook.select(idx)
                break