import tkinter as tk
import tkinter.ttk as ttk
from components.base_tab_frame import BaseTabFrame
from models.crud import select, get_column_names, get_table_names
from components.extended_treeview import ExtendedTreeview

class TableViewPage(BaseTabFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tk.Label(self, text="Table View Page", font=("Arial", 16)).pack(pady=20)
        tk.Button(
            self, text="Back to Home",
            command=lambda: controller.show_frame("HomePage")
        ).pack(pady=5)

        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(self, textvariable=self.table_var, state="readonly")
        self.table_dropdown.pack(pady=5)
        self.select_btn = tk.Button(self, text="Select Table", command=self.show_selected_table)
        self.select_btn.pack(pady=5)

        self.tree = None
        # Always try to populate dropdown on init
        self.populate_table_dropdown()

    def set_db_connection(self, db):
        super().set_db_connection(db)
        self.populate_table_dropdown()

    def populate_table_dropdown(self):
        # Try to get tables from cached connection if available
        if self.db_connection is not None and hasattr(self.db_connection, 'conn_cached') and self.db_connection.conn_cached is not None:
            tables = get_table_names(self.db_connection.conn_cached)
            self.table_dropdown['values'] = tables
            if tables:
                self.table_var.set(tables[0])
        else:
            self.table_dropdown['values'] = []
            self.table_var.set('')

    def show_selected_table(self):
        if self.tree:
            self.tree.destroy()
        if self.db_connection is None or not hasattr(self.db_connection, 'conn_cached') or not hasattr(self.db_connection, 'conn_original'):
            tk.messagebox.showerror("Error", "No database connection.")
            return
        table = self.table_var.get()
        if not table:
            tk.messagebox.showerror("Error", "No table selected.")
            return
        columns = get_column_names(self.db_connection.conn_cached, table)
        rows = select(self.db_connection.conn_cached, table, columns=columns)
        self.tree = ExtendedTreeview(
            self,
            columns=columns,
            show='headings',
            editable=True,
            draggable=True,
            searchbar=True,
            db=self.db_connection.conn_original,  # Use original for updates
            table=table,
            primary_key=columns[0] if columns else None
        )
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        for row in rows:
            self.tree.insert('', 'end', values=tuple(row))
        self.tree.pack(pady=10, fill='x')