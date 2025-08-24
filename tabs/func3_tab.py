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
            text="Alliance Management: Manage alliances, members, and belts.",
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
        Load all alliances from the database and populate the dropdown.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT UID, Name FROM tblUmbrella")
        self.alliances = {row.UID: row.Name for row in cursor.fetchall()}
        self.alliance_combo["values"] = list(self.alliances.values())
        if self.alliances:
            self.alliance_combo.current(0)
            self.load_alliance()

    def get_selected_alliance_uid(self):
        """
        Get the UID of the currently selected alliance from the dropdown.
        Returns None if not found.
        """
        if not hasattr(self, "alliances") or not self.alliance_combo.get():
            return None
        name = self.alliance_combo.get()
        for uid, n in self.alliances.items():
            if n == name:
                return uid
        return None

    def load_alliance(self):
        """
        Load and display members and belts for the selected alliance.
        """
        uid = self.get_selected_alliance_uid()
        if not uid:
            return

        cursor = self.conn.cursor()
        # Members (with table aliases)
        cursor.execute("""
            SELECT m.UID, f.Name, m.Permanent, m.Active
            FROM tblUmbrellaMember AS m
            INNER JOIN tblFed AS f ON m.MemberUID = f.UID
            WHERE m.UmbrellaUID = ?
        """, (uid,))
        self.member_tree.delete(*self.member_tree.get_children())
        for row in cursor.fetchall():
            self.member_tree.insert("", tk.END, values=tuple(row))

        # Belts (with table aliases)
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
        # No table aliases
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
        ttk.Label(dialog, text="Select Federation:").pack(padx=10, pady=5)
        fed_combo = ttk.Combobox(dialog, values=[f"{row.UID}: {row.Name}" for row in options], state="readonly")
        fed_combo.pack(padx=10, pady=5)
        perm_var = tk.BooleanVar()
        act_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Permanent", variable=perm_var).pack(padx=10, pady=2)
        ttk.Checkbutton(dialog, text="Active", variable=act_var).pack(padx=10, pady=2)
        def add():
            val = fed_combo.get()
            if not val:
                return
            fed_uid = int(val.split(":")[0])
            # Get the next UID
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
            SELECT b.UID, b.Name, f.Name
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
        ttk.Label(dialog, text="Select Belt:").pack(padx=10, pady=5)
        belt_combo = ttk.Combobox(dialog, values=[f"{row.UID}: {row.Name} ({row[2]})" for row in options], state="readonly")
        belt_combo.pack(padx=10, pady=5)
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

        # Ask if user wants to reassign the belt to a federation
        if messagebox.askyesno("Reassign Belt", "Do you want to reassign this belt to a federation?"):
            # Show dialog with federation dropdown
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
            # Just remove from alliance, set AllianceUID to 0.0
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

