import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class Func3Tab(ttk.Frame):
    """
    Alliance Manager tab for managing alliances, their members, and belts.
    Provides UI and logic for selecting alliances, adding/removing members and belts.
    """
    def __init__(self, parent, app):
        """
        Initialize the Alliance Manager tab UI and widgets.
        """
        super().__init__(parent)
        self.app = app
        self.conn = None

        # Sidebar
        sidebar_frame = ttk.Frame(self)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ttk.Label(
            sidebar_frame,
            text="""The Alliance Manager can be used to add member feds and belts to existing alliances.
            \n\nFirst choose an alliance from the dropdown and click Load. Both members and belts will be shown.
            \n\nYou can add or remove members by using the buttons below the members table.
            \n\nTo add a belt, use the respective button below the table. When removing a belt, you can choose to reassign it to a federation. This has to be done, because by default if the AllianceUID is set, the fed uid gets set to 0. So if no fed is assigned, the belt will be in a limbo state between active but not being assigned to any fed in the save.
            """,
            wraplength=180,
            justify="left"
        ).pack(anchor="n", fill=tk.X, pady=10)

        # Main content frame
        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Alliance dropdown
        alliance_frame = ttk.Frame(main_frame)
        alliance_frame.pack(fill=tk.X, pady=5)
        ttk.Label(alliance_frame, text="Select Alliance:").pack(side=tk.LEFT)
        self.alliance_combo = ttk.Combobox(alliance_frame, state="readonly")
        self.alliance_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(alliance_frame, text="Load", command=self.load_alliance).pack(side=tk.LEFT, padx=5)

        # Members section
        member_frame = ttk.LabelFrame(main_frame, text="Members")
        member_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.LEFT)
        self.member_tree = ttk.Treeview(member_frame, columns=["UID", "Name", "Permanent", "Active"], show="headings", height=8)
        for col in ["UID", "Name", "Permanent", "Active"]:
            self.member_tree.heading(col, text=col)
            self.member_tree.column(col, width=100)
        self.member_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_frame = ttk.Frame(member_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Add Member", command=self.add_member_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Member", command=self.remove_member).pack(side=tk.LEFT, padx=2)

        # Belts section
        belt_frame = ttk.LabelFrame(main_frame, text="Belts")
        belt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.LEFT)
        self.belt_tree = ttk.Treeview(belt_frame, columns=["UID", "Name", "Fed"], show="headings", height=8)
        for col in ["UID", "Name", "Fed"]:
            self.belt_tree.heading(col, text=col)
            self.belt_tree.column(col, width=100)
        self.belt_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        belt_btn_frame = ttk.Frame(belt_frame)
        belt_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(belt_btn_frame, text="Add Belt", command=self.add_belt_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(belt_btn_frame, text="Remove Belt", command=self.remove_belt).pack(side=tk.LEFT, padx=2)

        # Load alliances if connection exists
        self.after(500, self.try_load_alliances)

    def try_load_alliances(self):
        """
        Attempt to load alliances if a DB connection exists.
        """
        self.conn = self.app.conn
        if self.conn:
            self.load_alliances()

    def load_alliances(self):
        """
        Load all alliances from the database and populate the dropdown, showing if they are active or not.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT UID, Name, Active FROM tblUmbrella")
        self.alliances = {row.UID: row.Name for row in cursor.fetchall()}
        cursor.execute("SELECT UID, Name, Active FROM tblUmbrella")
        alliance_display = []
        self.alliance_uid_map = {}
        for row in cursor.fetchall():
            status = "Active" if row.Active else "Inactive"
            display = f"{row.Name} ({status})"
            alliance_display.append(display)
            self.alliance_uid_map[display] = row.UID
        self.alliance_combo["values"] = alliance_display
        if alliance_display:
            self.alliance_combo.current(0)
            self.load_alliance()

    def get_selected_alliance_uid(self):
        """
        Get the UID of the currently selected alliance from the dropdown.
        Returns None if not found.
        """
        if not hasattr(self, "alliance_uid_map") or not self.alliance_combo.get():
            return None
        display = self.alliance_combo.get()
        return self.alliance_uid_map.get(display)

    def load_alliance(self):
        """
        Load and display members and belts for the selected alliance.
        """
        uid = self.get_selected_alliance_uid()
        if not uid:
            return

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.UID, f.Name, m.Permanent, m.Active
            FROM tblUmbrellaMember AS m
            INNER JOIN tblFed AS f ON m.MemberUID = f.UID
            WHERE m.UmbrellaUID = ?
        """, (uid,))
        self.member_tree.delete(*self.member_tree.get_children())
        for row in cursor.fetchall():
            self.member_tree.insert("", tk.END, values=tuple(row))

        cursor.execute("""
            SELECT b.UID, b.Name, f.Name
            FROM tblBelt AS b
            LEFT JOIN tblFed AS f ON b.Fed = f.UID
            WHERE b.AllianceUID = ?
        """, (uid,))
        self.belt_tree.delete(*self.belt_tree.get_children())
        for row in cursor.fetchall():
            self.belt_tree.insert("", tk.END, values=tuple(row))

    def add_member_dialog(self):
        """
        Open a dialog to add a new member (federation) to the selected alliance.
        """
        uid = self.get_selected_alliance_uid()
        if not uid:
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT UID, Name FROM tblFed
            WHERE UID NOT IN (
                SELECT MemberUID FROM tblUmbrellaMember WHERE UmbrellaUID = ?
            )
        """, (uid,))
        options = cursor.fetchall()
        if not options:
            messagebox.showinfo("No Federations", "No federations available to add.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Member")
        dialog.geometry("420x180")
        ttk.Label(dialog, text="Select Federation:").pack(padx=10, pady=5)
        fed_var = tk.StringVar()
        fed_combo = ttk.Combobox(dialog, values=[f"{row.UID}: {row.Name}" for row in options], state="normal", width=40, textvariable=fed_var)
        fed_combo.pack(padx=10, pady=5)
        def on_fed_keyrelease(event):
            val = fed_var.get().lower()
            filtered = [f"{row.UID}: {row.Name}" for row in options if val in row.Name.lower() or val in str(row.UID)]
            fed_combo['values'] = filtered
        fed_combo.bind('<KeyRelease>', on_fed_keyrelease)
        perm_var = tk.BooleanVar()
        act_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Permanent", variable=perm_var).pack(padx=10, pady=2)
        ttk.Checkbutton(dialog, text="Active", variable=act_var).pack(padx=10, pady=2)
        def add():
            val = fed_combo.get()
            if not val:
                return
            fed_uid = int(val.split(":")[0])
            cursor.execute("SELECT MAX(UID) FROM tblUmbrellaMember")
            max_uid = cursor.fetchone()[0]
            next_uid = (max_uid + 1) if max_uid is not None else 1
            cursor.execute(
                "INSERT INTO tblUmbrellaMember (UID, Recordname, UmbrellaUID, MemberUID, Permanent, Active) VALUES (?, ?, ?, ?, ?, ?)",
                (next_uid, f"{uid}_{fed_uid}", uid, fed_uid, int(perm_var.get()), int(act_var.get()))
            )
            self.conn.commit()
            dialog.destroy()
            self.load_alliance()
        ttk.Button(dialog, text="Add", command=add).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=2)

    def remove_member(self):
        """
        Remove the selected member from the alliance.
        """
        sel = self.member_tree.selection()
        if not sel:
            return
        member_uid = self.member_tree.item(sel[0], "values")[0]
        uid = self.get_selected_alliance_uid()
        if not uid:
            return
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM tblUmbrellaMember WHERE UmbrellaUID = ? AND UID = ?",
            (uid, member_uid)
        )
        self.conn.commit()
        self.load_alliance()

    def add_belt_dialog(self):
        """
        Open a dialog to add a new belt to the selected alliance.
        """
        uid = self.get_selected_alliance_uid()
        if not uid:
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT b.UID, b.Name, f.Initials
            FROM tblBelt AS b
            LEFT JOIN tblFed AS f ON b.Fed = f.UID
            WHERE b.AllianceUID IS NULL OR b.AllianceUID <> ?
        """, (uid,))
        options = cursor.fetchall()
        if not options:
            messagebox.showinfo("No Belts", "No belts available to add.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Belt")
        dialog.geometry("420x180")
        ttk.Label(dialog, text="Select Belt:").pack(padx=10, pady=5)
        belt_var = tk.StringVar()
        belt_combo = ttk.Combobox(dialog, values=[f"{row.UID}: {row.Name} [{row[2]}]" if row[2] else f"{row.UID}: {row.Name}" for row in options], state="normal", width=40, textvariable=belt_var)
        belt_combo.pack(padx=10, pady=5)
        def on_belt_keyrelease(event):
            val = belt_var.get().lower()
            filtered = [f"{row.UID}: {row.Name} [{row[2]}]" if row[2] else f"{row.UID}: {row.Name}" for row in options if val in row.Name.lower() or val in str(row.UID) or (row[2] and val in row[2].lower())]
            belt_combo['values'] = filtered
        belt_combo.bind('<KeyRelease>', on_belt_keyrelease)
        def add():
            val = belt_combo.get()
            if not val:
                return
            belt_uid = int(val.split(":")[0])
            cursor.execute(
                "UPDATE tblBelt SET AllianceUID = ? WHERE UID = ?",
                (uid, belt_uid)
            )
            self.conn.commit()
            dialog.destroy()
            self.load_alliance()
        ttk.Button(dialog, text="Add", command=add).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=2)

    def remove_belt(self):
        """
        Remove the selected belt from the alliance, with option to reassign to a federation.
        """
        sel = self.belt_tree.selection()
        if not sel:
            return
        belt_uid = self.belt_tree.item(sel[0], "values")[0]
        cursor = self.conn.cursor()

        if messagebox.askyesno("Reassign Belt", "Do you want to reassign this belt to a federation?"):
            dialog = tk.Toplevel(self)
            dialog.title("Select Federation")
            ttk.Label(dialog, text="Select Federation:").pack(padx=10, pady=5)
            cursor.execute("SELECT UID, Name FROM tblFed")
            feds = cursor.fetchall()
            fed_combo = ttk.Combobox(dialog, values=[f"{row.UID}: {row.Name}" for row in feds], state="readonly")
            fed_combo.pack(padx=10, pady=5)

            def assign_and_remove():
                val = fed_combo.get()
                if not val:
                    messagebox.showwarning("No selection", "Please select a federation.")
                    return
                fed_uid = int(val.split(":")[0])
                cursor.execute(
                    "UPDATE tblBelt SET AllianceUID = 0.0, Fed = ? WHERE UID = ?",
                    (fed_uid, belt_uid)
                )
                self.conn.commit()
                dialog.destroy()
                self.load_alliance()

            ttk.Button(dialog, text="Assign", command=assign_and_remove).pack(pady=5)
            ttk.Button(dialog, text="Cancel", command=lambda: [dialog.destroy(), self.load_alliance()]).pack(pady=2)
        else:
            cursor.execute(
                "UPDATE tblBelt SET AllianceUID = 0.0 WHERE UID = ?",
                (belt_uid,)
            )
            self.conn.commit()
            self.load_alliance()

    def reload_alliances(self, conn):
        """
        Reload alliances from the given DB connection.
        """
        self.conn = conn
        self.load_alliances()

    def clear(self):
        """
        Clear the member and belt tables and reset the alliance dropdown.
        """
        self.member_tree.delete(*self.member_tree.get_children())
        self.belt_tree.delete(*self.belt_tree.get_children())
        self.alliance_combo.set("")

