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
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=2)
        ttk.Button(btn_frame, text="Change Type/Owner", command=self.change_type_dialog).pack(side=tk.LEFT, padx=5)
        self.tree = ttk.Treeview(self, columns=["UID", "Name", "Owner", "School", "Dojo", "Centre"], show="headings")
        self.tree.heading("UID", text="UID")
        self.tree.column("UID", width=60) 
        for col in ["Name", "Owner", "School", "Dojo", "Centre"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_dojos(self):
        """
        Load dojos from the database and display them in the treeview.
        Only show active dojos.
        """
        self.conn = self.app.conn
        if not self.conn:
            messagebox.showerror("Error", "Connect to a database first.")
            return
        df = pd.read_sql("SELECT UID, Name, Owner, School, Dojo, Centre FROM tblDojo WHERE Active=1", self.conn)
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
        combo = ttk.Combobox(self.tree, values=[f"{uid}: {name}" for uid, name in owner_dict.items()], state="normal", width=40)
        combo.place(x=x, y=y, width=width, height=height)
        combo.focus()

        def on_owner_keyrelease(event):
            val = combo.get().lower()
            filtered = [f"{uid}: {name}" for uid, name in owner_dict.items() if val in name.lower() or val in str(uid)]
            combo['values'] = filtered

        combo.bind('<KeyRelease>', on_owner_keyrelease)

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

    def change_type_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Row", "Please select a dojo to change type.")
            return
        item_id = selected[0]
        row_idx = self.tree.index(item_id)
        dojo_row = self.df.iloc[row_idx]
        dialog = tk.Toplevel(self)
        dialog.title("Change Dojo Type")
        dialog.geometry("400x220")
        ttk.Label(dialog, text="Select new type:").pack(pady=5)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(dialog, values=["School", "Dojo", "Centre"], textvariable=type_var, state="readonly")
        type_combo.pack(pady=5)
        owner_label = ttk.Label(dialog, text="Select new owner:")
        owner_label.pack(pady=5)
        owner_var = tk.StringVar()
        owner_combo = ttk.Combobox(dialog, state="normal", width=40, textvariable=owner_var)
        owner_combo.pack(pady=5)
        def update_owner_options(*args):
            if type_var.get() == "School":
                cursor = self.conn.cursor()
                cursor.execute("SELECT UID, Name FROM tblWorker")
                owners = cursor.fetchall()
                cursor.close()
            else:
                cursor = self.conn.cursor()
                cursor.execute("SELECT UID, Name FROM tblFed")
                owners = cursor.fetchall()
                cursor.close()
            owner_dict = {str(uid): name for uid, name in owners}
            owner_combo['values'] = [f"{uid}: {name}" for uid, name in owner_dict.items()]
            def on_owner_keyrelease(event):
                val = owner_var.get().lower()
                filtered = [f"{uid}: {name}" for uid, name in owner_dict.items() if val in name.lower() or val in str(uid)]
                owner_combo['values'] = filtered
            owner_combo.bind('<KeyRelease>', on_owner_keyrelease)
        type_combo.bind('<<ComboboxSelected>>', update_owner_options)
        def apply():
            t = type_var.get()
            o = owner_var.get()
            if not t or not o:
                messagebox.showwarning("Missing", "Select both type and owner.")
                return
            uid = int(o.split(":")[0])
            dojo_uid = int(self.df.iat[row_idx, 0])
            school, dojo, centre = 0, 0, 0
            if t == "School":
                school = 1
            elif t == "Dojo":
                dojo = 1
            elif t == "Centre":
                centre = 1
            sql = "UPDATE tblDojo SET School=?, Dojo=?, Centre=?, Owner=? WHERE UID=?"
            cur2 = self.conn.cursor()
            cur2.execute(sql, (school, dojo, centre, uid, dojo_uid))
            self.conn.commit()
            # Update UI
            values = list(self.tree.item(item_id, "values"))
            values[2] = uid
            values[3] = school
            values[4] = dojo
            values[5] = centre
            self.tree.item(item_id, values=values)
            self.df.iat[row_idx, 2] = uid
            self.df.iat[row_idx, 3] = school
            self.df.iat[row_idx, 4] = dojo
            self.df.iat[row_idx, 5] = centre
            dialog.destroy()
        ttk.Button(dialog, text="Apply", command=apply).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
