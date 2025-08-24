import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class Func2Tab(ttk.Frame):
    """
    Dojo Manager tab for managing dojos, their owners, and types.
    Provides UI and logic for loading dojos and editing their owners.
    """
    def __init__(self, parent, app):
        """
        Initialize the Dojo Manager tab UI and widgets.
        """
        super().__init__(parent)
        self.app = app
        self.conn = None

        # Sidebar
        sidebar_frame = ttk.Frame(self)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ttk.Label(
            sidebar_frame,
            text="""The Dojo Manager can be used to change the owner of a dojo/school/performance centre." \
            \n\nFirst load the dojos. Then double-click on the owner field. A dropdown will appear with possible owners.
            \n\nSchools can have workers as owners, while dojos and PCs are owned by federations.
            \n\nIf the dropdowns are to messe, search out the id of the worker or fed in the general tab.
            """,
            wraplength=180,
            justify="left"
        ).pack(anchor="n", fill=tk.X, pady=10)

        ttk.Button(self, text="Load Dojos", command=self.load_dojos).pack(pady=5)
        self.tree = ttk.Treeview(self, columns=["UID", "Name", "Owner", "School", "Dojo", "Centre"], show="headings")
        for col in ["UID", "Name", "Owner", "School", "Dojo", "Centre"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_dojos(self):
        """
        Load dojos from the database and display them in the treeview.
        """
        self.conn = self.app.conn
        if not self.conn:
            messagebox.showerror("Error", "Connect to a database first.")
            return
        df = pd.read_sql("SELECT UID, Name, Owner, School, Dojo, Centre FROM tblDojo", self.conn)
        self.df = df
        self.tree.delete(*self.tree.get_children())
        for _, row in df.iterrows():
            self.tree.insert("", tk.END, values=list(row))

    def on_double_click(self, event):
        """
        Handle double-click events on the treeview for editing the Owner field.
        Shows a dropdown of possible owners based on dojo type.
        """
        item_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not item_id or not col_id:
            return
        col_index = int(col_id.replace("#", "")) - 1
        col_name = self.df.columns[col_index]
        if col_name != "Owner":
            return  # Only allow editing Owner

        row_idx = self.tree.index(item_id)
        dojo_row = self.df.iloc[row_idx]
        is_school = bool(dojo_row["School"])
        is_dojo = bool(dojo_row["Dojo"])
        is_centre = bool(dojo_row["Centre"])

        # Query possible owners
        cursor = self.conn.cursor()
        if is_school:
            cursor.execute("SELECT UID, Name FROM tblWorker")
        elif is_dojo or is_centre:
            cursor.execute("SELECT UID, Name FROM tblFed")
        else:
            return
        owners = cursor.fetchall()
        owner_dict = {str(uid): name for uid, name in owners}

        x, y, width, height = self.tree.bbox(item_id, col_id)
        combo = ttk.Combobox(self.tree, values=[f"{uid}: {name}" for uid, name in owner_dict.items()], state="readonly")
        combo.place(x=x, y=y, width=width, height=height)
        combo.focus()

        def save_owner(event):
            val = combo.get()
            if not val:
                combo.destroy()
                return
            uid = int(val.split(":")[0])
            combo.destroy()
            values = list(self.tree.item(item_id, "values"))
            values[col_index] = uid
            self.tree.item(item_id, values=values)
            self.df.iat[row_idx, col_index] = uid
            try:
                dojo_uid = int(self.df.iat[row_idx, 0])  # Ensure Python int
                sql = "UPDATE tblDojo SET Owner = ? WHERE UID = ?"
                cur2 = self.conn.cursor()
                cur2.execute(sql, (int(uid), dojo_uid))  # Ensure both are Python int
                self.conn.commit()
            except Exception as e:
                messagebox.showerror("Update Error", str(e))

        combo.bind("<Return>", save_owner)
        combo.bind("<FocusOut>", lambda e: combo.destroy())
