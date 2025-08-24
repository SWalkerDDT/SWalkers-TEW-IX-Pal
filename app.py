import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyodbc
import pandas as pd
import re

from components.components import LabeledEntry
from tabs.func1_tab import Func1Tab
from tabs.func2_tab import Func2Tab
from tabs.func3_tab import Func3Tab

class MDBApp(tk.Tk):
    """
    Main application class for the MDB Tournament App.
    Handles the main window, tab setup, and general database operations.
    """

    def __init__(self):
        """
        Initialize the main application window, tabs, and variables.
        """
        super().__init__()
        self.title("SWalker's TEW IX Pal")
        self.geometry("1200x800")

        self.conn = None
        self.df = None
        self.tables = []
        self.current_table = None
        self.pk_col = None

        # Backup path variable
        self.backup_path_var = tk.StringVar()

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # General tab
        self.tab_general = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_general, text="Load Database File")
        self.build_general_tab(self.tab_general)

        # Func1 tab
        self.tab_func1 = Func1Tab(self.notebook, self)
        self.notebook.add(self.tab_func1, text="Round Robin Generator")

        # Func2 tab
        self.tab_func2 = Func2Tab(self.notebook, self)
        self.notebook.add(self.tab_func2, text="Dojo Manager")

        # Func3 tab
        self.tab_func3 = Func3Tab(self.notebook, self)
        self.notebook.add(self.tab_func3, text="Alliance Manager")

    # --- General tab ---
    def build_general_tab(self, parent):
        """
        Build the general tab UI for loading and connecting to the MDB file.
        """
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Sidebar (LEFT for General tab only)
        sidebar_frame = ttk.Frame(parent)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ttk.Label(
            sidebar_frame,
            text="""Welcome to the TEW IX Pal by SWalkerDDT.\nThis tool adds functions to edit some parts of TEW IX saves, that aren't easily editable in-game.
            \n\nFor using this tool, download and install the Microsoft Access Database Engine 2016 Redistributable from Microsoft's website is required.
            \n\nFirst load a TEW IX save file (MDB or ACCDB) using the 'Load Database File' tab. A backup will be created automatically in the 'backups' folder. There are two possibilities to choose from:
            \n1) Use a inital TEW9Save.mdb in your save game folder - make sure to not run this save file in TEW IX while using this tool, as it may corrupt the save.
            \n2) Use the TEW9Save.mdb in the temp/ Folder inside your save - this can be edited while the save is running, but make sure to not advance the current day as it may corrupt the save.
            \n\nYou can choose to edit the ODBC Driver and/or Password if needed - but usually the defaults should work. In the bottom table you can view the currently selected table, sort by columns or search for specific entries.
            \n\nFurther instructions for the other tabs can be found in their respective descriptions.
            """,
            wraplength=180,
            #justify="left"
        ).pack(anchor="n", fill=tk.X, pady=10)

        # File picker
        self.path_entry = LabeledEntry(control_frame, "MDB File:")
        self.path_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.browse_btn = ttk.Button(control_frame, text="Browse", command=self.load_file)
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        self.eject_btn = ttk.Button(control_frame, text="Eject", command=self.eject_file, state="disabled")
        self.eject_btn.pack(side=tk.LEFT, padx=5)

        # Backup display
        backup_frame = ttk.Frame(parent)
        backup_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(backup_frame, text="Last Backup:").pack(side=tk.LEFT)
        self.backup_entry = ttk.Entry(backup_frame, textvariable=self.backup_path_var, state="readonly", width=60)
        self.backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Driver
        driver_frame = ttk.Frame(parent)
        driver_frame.pack(fill=tk.X, padx=10, pady=5)
        self.driver_entry = LabeledEntry(driver_frame, "ODBC Driver:")
        self.driver_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.driver_entry.set("{Microsoft Access Driver (*.mdb, *.accdb)}")
        self.driver_entry.entry.config(state="disabled")
        self.driver_edit_var = tk.BooleanVar(value=False)
        def on_driver_toggle():
            if self.driver_edit_var.get():
                if messagebox.askyesno("Are you sure?", "Are you sure?"):
                    self.driver_entry.entry.config(state="normal")
                else:
                    self.driver_edit_var.set(False)
            else:
                self.driver_entry.entry.config(state="disabled")
        driver_check = ttk.Checkbutton(driver_frame, variable=self.driver_edit_var, command=on_driver_toggle)
        driver_check.pack(side=tk.LEFT, padx=5)

        # Password
        password_frame = ttk.Frame(parent)
        password_frame.pack(fill=tk.X, padx=10, pady=5)
        self.password_entry = LabeledEntry(password_frame, "Password:")
        self.password_entry.set("20YearsOfTEW")
        self.password_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.password_entry.entry.config(state="disabled")
        self.password_edit_var = tk.BooleanVar(value=False)
        def on_password_toggle():
            if self.password_edit_var.get():
                if messagebox.askyesno("Are you sure?", "Are you sure?"):
                    self.password_entry.entry.config(state="normal")
                else:
                    self.password_edit_var.set(False)
            else:
                self.password_entry.entry.config(state="disabled")
        password_check = ttk.Checkbutton(password_frame, variable=self.password_edit_var, command=on_password_toggle)
        password_check.pack(side=tk.LEFT, padx=5)

        # Table chooser
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(table_frame, text="Select Table:").pack(side=tk.LEFT, padx=5)
        self.table_combo = ttk.Combobox(table_frame, state="readonly")
        self.table_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.table_combo.bind("<<ComboboxSelected>>", self.on_table_selected)

        ttk.Button(parent, text="Connect MDB", command=self.connect_mdb).pack(pady=5)

        # Treeview
        self.tree = ttk.Treeview(parent)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        #self.tree.bind("<Double-1>", self.on_double_click)

        # Search bar
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(search_frame, text="Go", command=self.apply_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)

    def apply_search(self):
        """
        Apply a search filter to the currently loaded DataFrame and update the treeview.
        Supports AND/OR and column-specific queries.
        """
        if self.df is None:
            return
        query = self.search_var.get().strip()
        if not query:
            self.populate_tree()
            return
        df = self.df

        # Split by OR first (case-insensitive)
        or_parts = re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)
        result_indices = set()

        for or_part in or_parts:
            # Split by AND (case-insensitive)
            and_parts = re.split(r'\s+AND\s+', or_part, flags=re.IGNORECASE)
            mask = pd.Series([True] * len(df))
            for cond in and_parts:
                cond = cond.strip()
                m = re.match(r"(\w+)\s*=\s*'([^']*)'", cond)
                if m and m.group(1) in df.columns:
                    col, val = m.group(1), m.group(2)
                    mask &= (df[col].astype(str) == val)
                elif cond:
                    # General keyword search (any column contains term)
                    mask &= df.apply(lambda row: cond.lower() in str(row).lower(), axis=1)
            result_indices |= set(df[mask].index)

        filtered = df.loc[list(result_indices)]
        self.tree.delete(*self.tree.get_children())
        for _, row in filtered.iterrows():
            self.tree.insert("", tk.END, values=list(row))

    def clear_search(self):
        """
        Clear the search bar and repopulate the treeview with all data.
        """
        self.search_var.set("")
        self.populate_tree()

    def load_file(self):
        """
        Open a file dialog to select an MDB file, create a backup, and update the UI state.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Access Database", "*.mdb;*.accdb")],
            title="Select an MDB file"
        )
        if file_path:
            # Disable file input and browse button, enable eject
            self.path_entry.set(file_path)
            self.path_entry.entry.config(state="disabled")
            self.browse_btn.config(state="disabled")
            self.eject_btn.config(state="normal")

            # Create backup
            top_folder = os.path.basename(os.path.dirname(file_path))
            now = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            backup_dir = os.path.join("backups", top_folder, now)
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_file)
            self.backup_path_var.set(backup_file)

    def eject_file(self):
        """
        Eject the current database connection and clear all UI fields and tables.
        """
        # Close DB connection
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

        # Clear all fields and trees
        self.path_entry.set("")
        self.path_entry.entry.config(state="normal")
        self.browse_btn.config(state="normal")
        self.eject_btn.config(state="disabled")
        self.backup_path_var.set("")
        self.driver_entry.set("{Microsoft Access Driver (*.mdb, *.accdb)}")
        self.driver_entry.entry.config(state="disabled")
        self.driver_edit_var.set(False)
        self.password_entry.set("20YearsOfTEW")
        self.password_entry.entry.config(state="disabled")
        self.password_edit_var.set(False)
        self.table_combo.set("")
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []
        self.tree["show"] = ""
        if hasattr(self, "tab_func1"):
            self.tab_func1.participant_tree.delete(*self.tab_func1.participant_tree.get_children())
            self.tab_func1.combined_tree.delete(*self.tab_func1.combined_tree.get_children())
            self.tab_func1.tourney_combo.set("")
            self.tab_func1.match_combo.set("")
        if hasattr(self, "tab_func2"):
            self.tab_func2.tree.delete(*self.tab_func2.tree.get_children())
        if hasattr(self, "tab_func3"):
            self.tab_func3.member_tree.delete(*self.tab_func3.member_tree.get_children())
            self.tab_func3.belt_tree.delete(*self.tab_func3.belt_tree.get_children())
            self.tab_func3.alliance_combo.set("")

    def connect_mdb(self):
        """
        Connect to the selected MDB file using the provided driver and password.
        Loads available tables and updates tabs with the connection.
        """
        db_file = self.path_entry.get()
        driver = self.driver_entry.get()
        password = self.password_entry.get()
        if not db_file:
            messagebox.showwarning("No file", "Select an MDB file first.")
            return

        try:
            conn_str = f'DRIVER={driver};DBQ={db_file};UID={""};PWD={password};'
            self.conn = pyodbc.connect(conn_str)
            cursor = self.conn.cursor()
            self.tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
            if not self.tables:
                messagebox.showinfo("No tables", "No tables found in MDB.")
                return
            self.table_combo["values"] = self.tables
            self.table_combo.current(0)
            self.current_table = self.tables[0]
            self.load_table(self.current_table)

            # Also provide connection to Func1 tab
            self.tab_func1.conn = self.conn
            self.tab_func1.load_tournaments()

            # Also provide connection to Func3 tab and reload alliances
            self.tab_func3.reload_alliances(self.conn)

        except Exception as e:
            messagebox.showerror("Error", f"Could not connect:\n{e}")

    def on_table_selected(self, event=None):
        """
        Callback for when a table is selected from the dropdown. Loads the selected table.
        """
        table = self.table_combo.get()
        if table:
            self.current_table = table
            self.load_table(table)

    def load_table(self, table):
        """
        Load the selected table from the database into a DataFrame and display it in the treeview.
        """
        try:
            self.df = pd.read_sql(f"SELECT * FROM [{table}]", self.conn)
            self.pk_col = self.df.columns[0]  # assume first col is PK
            self.populate_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load table {table}:\n{e}")

    def populate_tree(self):
        """
        Populate the treeview with the current DataFrame.
        """
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(self.df.columns)
        self.tree["show"] = "headings"
        for col in self.df.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))
            self.tree.column(col, width=120)
        for _, row in self.df.iterrows():
            self.tree.insert("", tk.END, values=list(row))

    def sort_by_column(self, col, reverse):
        """
        Sort the DataFrame by the given column and update the treeview.
        """
        # Sort DataFrame and update tree
        self.df.sort_values(by=col, ascending=not reverse, inplace=True, kind='mergesort')
        self.populate_tree()
        # Reverse sort next time
        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def on_double_click(self, event):
        """
        Handle double-click events on the treeview for inline editing of cell values.
        """
        item_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not item_id or not col_id:
            return
        col_index = int(col_id.replace("#", "")) - 1
        col_name = self.df.columns[col_index]
        x, y, width, height = self.tree.bbox(item_id, col_id)
        value = self.tree.item(item_id, "values")[col_index]
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, value)
        entry.focus()

        def save_edit(event):
            new_val = entry.get()
            entry.destroy()
            values = list(self.tree.item(item_id, "values"))
            values[col_index] = new_val
            self.tree.item(item_id, values=values)
            row_idx = self.tree.index(item_id)
            self.df.iat[row_idx, col_index] = new_val
            try:
                pk_val = self.df.iat[row_idx, 0]
                sql = f"UPDATE [{self.current_table}] SET [{col_name}] = ? WHERE [{self.pk_col}] = ?"
                cursor = self.conn.cursor()
                cursor.execute(sql, (new_val, pk_val))
                self.conn.commit()
            except Exception as e:
                messagebox.showerror("Update Error", str(e))

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())


if __name__ == "__main__":
    app = MDBApp()
    app.mainloop()
