import tkinter as tk
import tkinter.ttk as ttk
from components.base_tab_frame import BaseTabFrame
from models.crud import select, get_column_names
from components.extended_treeview import ExtendedTreeview

class SettingsPage(BaseTabFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tk.Label(self, text="Settings Page", font=("Arial", 16)).pack(pady=20)
        tk.Button(
            self, text="Back to Home",
            command=lambda: controller.show_frame("HomePage")
        ).pack(pady=5)

        tk.Button(
            self, text="Show All Workers",
            command=self.show_all_workers
        ).pack(pady=10)

        self.tree = None

    def show_all_workers(self):
        if self.tree:
            self.tree.destroy()
        if self.db_connection is None:
            tk.messagebox.showerror("Error", "No database connection.")
            return
        all_columns = get_column_names(self.db_connection, 'tblWorker')
        print("All columns:", all_columns)
        display_columns = [col for col in all_columns if col in ['UID', 'Name']]
        rows = select(self.db_connection, 'tblWorker', columns=display_columns)
        self.tree = ExtendedTreeview(
            self,
            columns=display_columns,
            show='headings',
            editable=True,
            draggable=True,
            db=self.db_connection,
            table='tblWorker',
            primary_key='UID'
        )
        for col in display_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        for row in rows:
            self.tree.insert('', 'end', values=tuple(row))
        self.tree.pack(pady=10, fill='x')
