import tkinter as tk
from tkinter import ttk, messagebox
import random
import pyodbc
from utils.round_robin import (
    clear_pre_booking,
)

class Func6Tab(ttk.Frame):
    """
    Wrestling Card Builder for creating a custom card with matches and participants.
    Provides UI for building a card, managing matches, and booking them into the database.
    """
    def __init__(self, parent, app):
        """
        Initialize the Wrestling Card Builder tab UI and variables.
        """
        super().__init__(parent)
        self.app = app
        self.conn = None
        self.feds = {}
        self.selected_fed = tk.StringVar()
        self.matches = []  # List of dicts: {type, side1, side2, winner, length, checked}
        self._build_ui()
        self.after(500, self.refresh)

    def _build_ui(self):
        """
        Build the user interface for the Wrestling Card Builder tab.
        """
        ttk.Label(self, text="Wrestling Card Builder").pack(pady=5)
        fed_frame = ttk.Frame(self)
        fed_frame.pack(pady=2)
        ttk.Label(fed_frame, text="User Promotion:").pack(side=tk.LEFT)
        self.fed_combo = ttk.Combobox(fed_frame, state="readonly", textvariable=self.selected_fed)
        self.fed_combo.pack(side=tk.LEFT, padx=5)
        self.fed_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        # Table for matches
        self.matches = []  # List of dicts: {type, side1, side2, winner, length, checked}
        self.match_tree = ttk.Treeview(self, columns=["Book", "Type", "Side1", "Side2", "Winner", "Length"], show="headings", height=8)
        for col in ["Book", "Type", "Side1", "Side2", "Winner", "Length"]:
            self.match_tree.heading(col, text=col)
            self.match_tree.column(col, width=80 if col == "Book" else 160)
        self.match_tree.pack(fill=tk.X, padx=5, pady=2)
        self.match_tree.bind('<Button-1>', self.on_tree_click)
        arrow_frame = ttk.Frame(self)
        arrow_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(arrow_frame, text="↑", width=3, command=self.move_match_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(arrow_frame, text="↓", width=3, command=self.move_match_down).pack(side=tk.LEFT, padx=2)
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Add Match", command=self.add_match_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Remove Selected", command=self.remove_selected_match).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Update Entry", command=self.update_selected_match).pack(side=tk.LEFT, padx=2)
        ttk.Button(self, text="Book Matches", command=self.book_matches).pack(pady=8)
        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(pady=2)

    def refresh(self):
        """
        Refresh the tab by reloading promotions from the database.
        """
        self.conn = self.app.conn
        if self.conn:
            self.load_feds()

    def load_feds(self):
        """
        Load user-controlled promotions from the database and update the combobox.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT UID, Name FROM tblFed WHERE User_Controlled = 1")
        self.feds = {str(row.UID): row.Name for row in cursor.fetchall()}
        values = list(self.feds.values())
        current = self.selected_fed.get()
        self.fed_combo['values'] = values
        if values:
            if current not in values:
                self.selected_fed.set(values[0])
            self.fed_combo.set(self.selected_fed.get())
        else:
            self.selected_fed.set("")
            self.fed_combo.set("")
        self.fed_combo.update_idletasks()
        cursor.close()

    def get_selected_fed_uid(self):
        """
        Get the UID of the currently selected promotion.
        Returns:
            int or None: UID of the selected promotion, or None if not found.
        """
        name = self.selected_fed.get()
        for uid, n in self.feds.items():
            if n == name:
                return int(uid)
        return None

    def add_match_dialog(self, prefill=None, on_update=None):
        """
        Open a dialog to add or update a match entry.
        Args:
            prefill (dict, optional): Data to prefill the dialog for updating.
            on_update (callable, optional): Callback for updating an existing match.
        """
        dialog = tk.Toplevel(self)
        dialog.title("Add Match" if not prefill else "Update Match")
        # Make the dialog bigger
        dialog.geometry("800x800")
        ttk.Label(dialog, text="Match Type:").pack(pady=2)
        type_var = tk.StringVar(value=prefill["type"] if prefill else "1v1")
        type_combo = ttk.Combobox(dialog, values=["1v1", "2v2", "3v3", "4v4", "5v5"], textvariable=type_var, state="readonly")
        type_combo.pack(pady=2)
        # Match dropdown
        ttk.Label(dialog, text="Match:").pack(pady=2)
        match_var = tk.StringVar()
        match_combo = ttk.Combobox(dialog, textvariable=match_var, state="readonly", width=40)
        match_combo.pack(pady=2)
        match_uid_map = {}
        def update_match_combo(*args):
            fed_uid = self.get_selected_fed_uid()
            if not fed_uid:
                match_combo['values'] = []
                return
            cursor = self.conn.cursor()
            mtype_map = {"1v1": 1, "2v2": 2, "3v3": 3, "4v4": 4, "5v5": 5}
            mtype_val = mtype_map.get(type_var.get(), 1)
            cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = ?", (mtype_val,))
            matches = [(row.UID, row.Name) for row in cursor.fetchall()]
            match_uid_map.clear()
            match_combo['values'] = [name for uid, name in matches]
            for uid, name in matches:
                match_uid_map[name] = uid
            # Set prefill or default
            if prefill and prefill.get("match_uid"):
                for uid, name in matches:
                    if uid == prefill["match_uid"]:
                        match_var.set(name)
                        match_combo.set(name)
                        break
                else:
                    if matches:
                        match_var.set(matches[0][1])
                        match_combo.set(matches[0][1])
                    else:
                        match_var.set("")
                        match_combo.set("")
            elif matches:
                match_var.set(matches[0][1])
                match_combo.set(matches[0][1])
            else:
                match_var.set("")
                match_combo.set("")
        type_combo.bind('<<ComboboxSelected>>', update_match_combo)
        update_match_combo()
        # Side 1
        ttk.Label(dialog, text="Side 1:").pack(pady=2)
        side1_frame = ttk.Frame(dialog)
        side1_frame.pack(fill=tk.X, padx=5)
        # Make the side tables bigger (height=8, wider columns)
        side1_tree = ttk.Treeview(side1_frame, columns=["Type", "Name", "ID"], show="headings", height=8)
        for col in ["Type", "Name", "ID"]:
            side1_tree.heading(col, text=col)
            side1_tree.column(col, width=150 if col != "ID" else 100)
        side1_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        s1_btns = ttk.Frame(side1_frame)
        s1_btns.pack(side=tk.LEFT, padx=2, fill=tk.Y)
        def add_side1():
            self._add_side_entry(side1_tree, dialog)
        def remove_side1():
            sel = side1_tree.selection()
            for s in sel:
                side1_tree.delete(s)
        ttk.Button(s1_btns, text="+", command=add_side1).pack(pady=2)
        ttk.Button(s1_btns, text="-", command=remove_side1).pack(pady=2)
        # Side 2
        ttk.Label(dialog, text="Side 2:").pack(pady=2)
        side2_frame = ttk.Frame(dialog)
        side2_frame.pack(fill=tk.X, padx=5)
        # Make the side tables bigger (height=8, wider columns)
        side2_tree = ttk.Treeview(side2_frame, columns=["Type", "Name", "ID"], show="headings", height=8)
        for col in ["Type", "Name", "ID"]:
            side2_tree.heading(col, text=col)
            side2_tree.column(col, width=150 if col != "ID" else 100)
        side2_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        s2_btns = ttk.Frame(side2_frame)
        s2_btns.pack(side=tk.LEFT, padx=2, fill=tk.Y)
        def add_side2():
            self._add_side_entry(side2_tree, dialog)
        def remove_side2():
            sel = side2_tree.selection()
            for s in sel:
                side2_tree.delete(s)
        ttk.Button(s2_btns, text="+", command=add_side2).pack(pady=2)
        ttk.Button(s2_btns, text="-", command=remove_side2).pack(pady=2)
        # Winner dropdown
        ttk.Label(dialog, text="Winner:").pack(pady=2)
        winner_var = tk.StringVar(value=prefill["winner"] if prefill else "")
        winner_combo = ttk.Combobox(dialog, textvariable=winner_var, state="readonly", width=20)
        winner_combo['values'] = ["Side 1", "Side 2"]
        winner_combo.pack(pady=2)
        # Length
        ttk.Label(dialog, text="Length (minutes):").pack(pady=2)
        length_var = tk.StringVar(value=str(prefill["length"]) if prefill else "10")
        ttk.Entry(dialog, textvariable=length_var, width=10).pack(pady=2)
        # Prefill sides
        if prefill:
            for t, n, id_ in prefill["side1"]:
                side1_tree.insert("", tk.END, values=(t, n, id_))
            for t, n, id_ in prefill["side2"]:
                side2_tree.insert("", tk.END, values=(t, n, id_))
        # Add/Update button
        def add_or_update():
            mtype = type_var.get()
            match_name = match_var.get()
            match_uid = match_uid_map.get(match_name)
            def get_side(tree):
                entries = []
                for iid in tree.get_children():
                    t, n, id_ = tree.item(iid, "values")
                    entries.append((t, n, id_))
                return entries
            side1 = get_side(side1_tree)
            side2 = get_side(side2_tree)
            # Determine required number for each side
            mtype_map = {"1v1": 1, "2v2": 2, "3v3": 3, "4v4": 4, "5v5": 5}
            req_num = mtype_map.get(mtype, 1)
            # Fill missing spots with random workers
            fed_uid = self.get_selected_fed_uid()
            cursor = self.conn.cursor()
            cursor.execute("SELECT tblWorker.UID, tblWorker.Name FROM tblContract INNER JOIN tblWorker ON tblContract.WorkerUID = tblWorker.UID WHERE tblContract.FedUID = ? AND tblContract.Position_Wrestler = 1", (fed_uid,))
            all_workers = [(str(row[0]), row[1]) for row in cursor.fetchall()]
            def fill_side(side):
                existing_ids = set(id_ for t, n, id_ in side)
                available = [(wid, wname) for wid, wname in all_workers if wid not in existing_ids]
                while len(side) < req_num and available:
                    wid, wname = random.choice(available)
                    side.append(("Worker", wname, wid))
                    available = [(wid2, wname2) for wid2, wname2 in available if wid2 != wid]
                return side[:req_num]
            side1 = fill_side(side1)
            side2 = fill_side(side2)
            winner = winner_var.get()
            try:
                length = int(length_var.get())
            except Exception:
                messagebox.showerror("Error", "Invalid match length.")
                return
            new_data = {
                "type": mtype,
                "side1": side1,
                "side2": side2,
                "winner": winner,
                "length": length,
                "match_uid": match_uid,
                "checked": True
            }
            if on_update:
                on_update(new_data)
            else:
                def side_display(side):
                    return ", ".join([n for t, n, id_ in side])
                values = ("✔", mtype, side_display(side1), side_display(side2), winner, length)
                self.matches.append(new_data)
                self.match_tree.insert("", tk.END, values=values)
            dialog.destroy()
        ttk.Button(dialog, text="Update" if prefill else "Add", command=add_or_update).pack(pady=5)
        ttk.Button(dialog, text="Cancel")

    def _add_side_entry(self, tree, parent_dialog):
        """
        Open a dialog to add a participant (worker, stable, or team) to a match side.
        Args:
            tree (ttk.Treeview): The treeview to add the entry to.
            parent_dialog (tk.Toplevel): The parent dialog window.
        """
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Side Entry")
        dialog.geometry("350x180")
        ttk.Label(dialog, text="Type:").pack(pady=2)
        type_var = tk.StringVar(value="Worker")
        type_combo = ttk.Combobox(dialog, values=["Worker", "Stable", "Team"], textvariable=type_var, state="readonly")
        type_combo.pack(pady=2)
        ttk.Label(dialog, text="Select:").pack(pady=2)
        select_var = tk.StringVar()
        # Make the Combobox searchable
        select_combo = ttk.Combobox(dialog, textvariable=select_var, state="normal", width=28)
        select_combo.pack(pady=2)
        self._side_entry_cache = getattr(self, '_side_entry_cache', {})
        def update_select():
            t = type_var.get()
            fed_uid = self.get_selected_fed_uid()
            cursor = self.conn.cursor()
            if t == "Worker":
                cursor.execute("SELECT tblWorker.UID, tblWorker.Name FROM tblContract INNER JOIN tblWorker ON tblContract.WorkerUID = tblWorker.UID WHERE tblContract.FedUID = ? AND tblContract.Position_Wrestler = 1", (fed_uid,))
                wrestlers = [(row[0], row[1]) for row in cursor.fetchall()]
                select_combo['values'] = [f"{wid}: {name}" for wid, name in wrestlers]
                self._side_entry_cache['workers'] = wrestlers
            elif t == "Stable":
                cursor.execute("SELECT UID, Name FROM tblStable WHERE Fed = ? AND Active = 1", (fed_uid,))
                stables = [(row[0], row[1]) for row in cursor.fetchall()]
                select_combo['values'] = [f"{sid}: {name}" for sid, name in stables]
                self._side_entry_cache['stables'] = stables
            elif t == "Team":
                cursor.execute("SELECT UID, Name, Worker1, Worker2 FROM tblTeam WHERE Fed = ? AND Active = 1", (fed_uid,))
                teams = []
                for row in cursor.fetchall():
                    tid, tname, w1, w2 = row
                    valid = True
                    for wid in [w1, w2]:
                        if wid and wid != 0:
                            cursor.execute("SELECT 1 FROM tblContract WHERE WorkerUID = ? AND FedUID = ? AND Position_Wrestler = 1", (wid, fed_uid))
                            if not cursor.fetchone():
                                valid = False
                                break
                    if valid:
                        teams.append((tid, tname))
                select_combo['values'] = [f"{tid}: {tname}" for tid, tname in teams]
                self._side_entry_cache['teams'] = teams
        type_combo.bind('<<ComboboxSelected>>', lambda e: update_select())
        update_select()
        # Add filtering to the combobox
        def on_select_keyrelease(event):
            value = select_var.get().lower()
            all_values = select_combo['values']
            filtered = [v for v in all_values if value in v.lower()]
            select_combo['values'] = filtered if filtered else all_values
        select_combo.bind('<KeyRelease>', on_select_keyrelease)
        def add():
            t = type_var.get()
            val = select_var.get()
            if not val:
                messagebox.showwarning("No selection", "Please select an entry to add.")
                return
            id_ = val.split(":")[0]
            name = val.split(":", 1)[1].strip()
            fed_uid = self.get_selected_fed_uid()
            cursor = self.conn.cursor()
            if t == "Worker":
                tree.insert("", tk.END, values=(t, name, id_))
            elif t == "Team":
                cursor.execute("SELECT Worker1, Worker2 FROM tblTeam WHERE UID = ? AND Active = 1", (int(id_),))
                row = cursor.fetchone()
                member_ids = [wid for wid in row if wid and wid != 0]
                for wid in member_ids:
                    cursor.execute("SELECT Name FROM tblWorker WHERE UID = ?", (wid,))
                    wname = cursor.fetchone()[0]
                    tree.insert("", tk.END, values=("Worker", wname, wid))
            elif t == "Stable":
                cursor.execute("SELECT " + ", ".join([f"Member{i}" for i in range(1, 11)]) + " FROM tblStable WHERE UID = ? AND Active = 1", (int(id_),))
                row = cursor.fetchone()
                member_ids = [wid for wid in row if wid]
                random.shuffle(member_ids)
                for wid in member_ids:
                    cursor.execute("SELECT Name FROM tblWorker WHERE UID = ?", (wid,))
                    wname = cursor.fetchone()[0]
                    tree.insert("", tk.END, values=("Worker", wname, wid))
            dialog.destroy()
        ttk.Button(dialog, text="Add", command=add).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=2)

    def remove_selected_match(self):
        """
        Remove the selected match from the match list and treeview.
        """
        sel = self.match_tree.selection()
        for s in sel:
            idx = self.match_tree.index(s)
            self.match_tree.delete(s)
            if idx < len(self.matches):
                self.matches.pop(idx)

    def update_selected_match(self):
        """
        Open a dialog to update the selected match entry.
        """
        sel = self.match_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a match to update.")
            return
        idx = self.match_tree.index(sel[0])
        if idx >= len(self.matches):
            return
        match_data = self.matches[idx]
        def on_update(new_data):
            self.matches[idx] = new_data
            def side_display(side):
                return ", ".join([n for t, n, id_ in side])
            values = ("✔" if new_data.get("checked", True) else "", new_data["type"], side_display(new_data["side1"]), side_display(new_data["side2"]), new_data["winner"], new_data["length"])
            self.match_tree.item(sel[0], values=values)
        self.add_match_dialog(prefill=match_data, on_update=on_update)

    def on_tree_click(self, event):
        """
        Handle clicks on the match treeview, toggling the 'Book' checkbox.
        """
        region = self.match_tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.match_tree.identify_column(event.x)
            if col == "#1":  # Book column
                row = self.match_tree.identify_row(event.y)
                if row:
                    idx = self.match_tree.index(row)
                    self.matches[idx]["checked"] = not self.matches[idx].get("checked", True)
                    values = list(self.match_tree.item(row, "values"))
                    values[0] = "✔" if self.matches[idx]["checked"] else ""
                    self.match_tree.item(row, values=values)

    def book_matches(self):
        """
        Book the checked matches in the order shown in the table.
        """
        checked_matches = []
        for item in self.match_tree.get_children():
            idx = self.match_tree.index(item)
            if self.matches[idx].get("checked", True):
                # Remove 'checked' key for auto_book
                match = {k: v for k, v in self.matches[idx].items() if k != "checked"}
                checked_matches.append(match)
        self.auto_book(matches=checked_matches)

    def auto_book(self, matches=None):
        """
        Book matches into the database, either from the table or using legacy logic if matches is None.
        Args:
            matches (list, optional): List of match dicts to book.
        """
        if not self.conn:
            messagebox.showerror("Error", "No database connection.")
            return
        fed_uid = self.get_selected_fed_uid()
        if not fed_uid:
            messagebox.showerror("Error", "No promotion selected.")
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT CardUID FROM tblTonightsSchedule WHERE FedUID = ?", (fed_uid,))
        card_uids = [row[0] for row in cursor.fetchall()]
        if not card_uids:
            messagebox.showinfo("No Show", "No user booked shows for this promotion tonight.")
            return
        # If matches are not provided, use the old logic (for legacy/auto)
        if matches is None:
            # Get wrestlers
            cursor.execute("SELECT WorkerUID, Face FROM tblContract WHERE FedUID = ? AND Position_Wrestler = 1", (fed_uid,))
            wrestlers = [(row[0], row[1]) for row in cursor.fetchall()]
            wrestler_ids = [w[0] for w in wrestlers]
            weights = {}
            perceptions = {}
            # Fill perceptions from tblContract
            cursor.execute("SELECT WorkerUID, Perception FROM tblContract WHERE FedUID = ? AND Position_Wrestler = 1", (fed_uid,))
            for row in cursor.fetchall():
                perceptions[row[0]] = row[1]
            # Get stables
            cursor.execute("SELECT * FROM tblStable WHERE Fed = ? AND Active = 1", (fed_uid,))
            stables = cursor.fetchall()
            # Get teams
            cursor.execute("SELECT * FROM tblTeam WHERE Fed = ? AND Active = 1", (fed_uid,))
            teams = cursor.fetchall()
            # Get weight limit
            cursor.execute("SELECT Junior_Weight FROM tblFedStyle WHERE FedUID = ?", (fed_uid,))
            row = cursor.fetchone()
            weight_limit = row[0] if row else None
            # Get announcers
            cursor.execute("SELECT Announce1, Announce2, Announce3 FROM tblFed WHERE UID = ?", (fed_uid,))
            ann = cursor.fetchone()
            announcer1 = ann[0] if ann else None
            announcer2 = ann[1] if ann else None
            announcer3 = ann[2] if ann else None
            # Get referees and road agents
            cursor.execute("SELECT WorkerUID FROM tblContract WHERE FedUID = ? AND Position_Referee = 1", (fed_uid,))
            referees = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT WorkerUID FROM tblContract WHERE FedUID = ? AND Position_Roadagent = 1", (fed_uid,))
            roadagents = [row[0] for row in cursor.fetchall()]
            # Booking logic
            num_matches = self.num_matches_var.get()
            singles = self.singles_var.get()
            tag = self.tag_var.get()
            three = self.three_var.get()
            four = self.four_var.get()
            five = self.five_var.get()
            if singles + tag + three + four + five != 100:
                messagebox.showerror("Error", "Percentages must sum to 100%.")
                return
            use_stables = self.use_stables_var.get()
            use_weight = self.use_weight_var.get()
            use_faceheel = self.use_faceheel_var.get()
            main_time = self.main_time_var.get()
            comain_time = self.comain_time_var.get()
            other_min = self.other_min_var.get()
            other_max = self.other_max_var.get()
            # Build match types list
            match_types = (["singles"] * (singles * num_matches // 100) +
                           ["tag"] * (tag * num_matches // 100) +
                           ["3v3"] * (three * num_matches // 100) +
                           ["4v4"] * (four * num_matches // 100) +
                           ["5v5"] * (five * num_matches // 100))
            while len(match_types) < num_matches:
                match_types.append("singles")
            random.shuffle(match_types)
            # Select wrestlers for matches
            booked_workers = set()
            matches = []
            # Build face/heel and weight maps
            face_map = {w[0]: w[1] for w in wrestlers}
            for mtype in match_types:
                pool = [w for w in wrestlers if w[0] not in booked_workers]
                if mtype == "singles":
                    # Weight limit logic
                    if use_weight and weight_limit:
                        hw = [w for w in pool if weights.get(w[0], 0) >= weight_limit]
                        jw = [w for w in pool if weights.get(w[0], 0) < weight_limit]
                        if len(hw) >= 2:
                            pool = hw
                        elif len(jw) >= 2:
                            pool = jw
                    # Face/Heel logic
                    if use_faceheel:
                        faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                        heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                        if faces and heels:
                            p1 = random.choice(faces)
                            p2 = random.choice(heels)
                            matches.append(([p1[0]], [p2[0]], mtype))
                            booked_workers.update([p1[0], p2[0]])
                            continue
                    # Fallback
                    if len(pool) < 2:
                        continue
                    p1, p2 = random.sample(pool, 2)
                    matches.append(([p1[0]], [p2[0]], mtype))
                    booked_workers.update([p1[0], p2[0]])
                elif mtype == "tag":
                    # Use stables if checked
                    if use_stables:
                        stable_teams = []
                        for s in stables:
                            members = [int(getattr(s, f'Member{i}')) for i in range(1, 11) if getattr(s, f'Member{i}', 0)]
                            members = [m for m in members if m in [w[0] for w in pool]]
                            if len(members) >= 2:
                                stable_teams.append(members)
                        random.shuffle(stable_teams)
                        used = set()
                        for t1 in stable_teams:
                            for t2 in stable_teams:
                                if t1 != t2 and not (set(t1[:2]) & set(t2[:2])) and len(t1) >= 2 and len(t2) >= 2:
                                    matches.append((t1[:2], t2[:2], mtype))
                                    booked_workers.update(t1[:2] + t2[:2])
                                    used.update(t1[:2] + t2[:2])
                                    break
                            if used:
                                break
                        if used:
                            continue
                    # Face/Heel logic
                    if use_faceheel:
                        faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                        heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                        if len(faces) >= 2 and len(heels) >= 2:
                            team1 = random.sample(faces, 2)
                            team2 = random.sample(heels, 2)
                            matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                            booked_workers.update([w[0] for w in team1 + team2])
                            continue
                    # Fallback
                    if len(pool) < 4:
                        continue
                    team1 = random.sample(pool, 2)
                    team2 = random.sample([w for w in pool if w not in team1], 2)
                    matches.append(([team1[0][0], team1[1][0]], [team2[0][0], team2[1][0]], mtype))
                    booked_workers.update([team1[0][0], team1[1][0], team2[0][0], team2[1][0]])
                elif mtype == "3v3":
                    # Use stables if checked
                    if use_stables:
                        stable_teams = []
                        for s in stables:
                            members = [int(getattr(s, f'Member{i}')) for i in range(1, 11) if getattr(s, f'Member{i}', 0)]
                            members = [m for m in members if m in [w[0] for w in pool]]
                            if len(members) >= 3:
                                stable_teams.append(members)
                        random.shuffle(stable_teams)
                        used = set()
                        for t1 in stable_teams:
                            for t2 in stable_teams:
                                if t1 != t2 and not (set(t1[:3]) & set(t2[:3])) and len(t1) >= 3 and len(t2) >= 3:
                                    matches.append((t1[:3], t2[:3], mtype))
                                    booked_workers.update(t1[:3] + t2[:3])
                                    used.update(t1[:3] + t2[:3])
                                    break
                            if used:
                                break
                        if used:
                            continue
                    # Face/Heel and weight logic
                    if use_faceheel or use_weight:
                        faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                        heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                        if use_weight and weight_limit:
                            def split_team(team):
                                hw = [w for w in team if weights.get(w[0], 0) >= weight_limit]
                                jw = [w for w in team if weights.get(w[0], 0) < weight_limit]
                                return hw, jw
                            if len(faces) >= 3 and len(heels) >= 3:
                                team1 = random.sample(faces, 3)
                                team2 = random.sample(heels, 3)
                                hw1, jw1 = split_team(team1)
                                hw2, jw2 = split_team(team2)
                                if abs(len(hw1) - len(hw2)) <= 1 and abs(len(jw1) - len(jw2)) <= 1:
                                    matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                                    booked_workers.update([w[0] for w in team1 + team2])
                                    continue
                        elif len(faces) >= 3 and len(heels) >= 3:
                            team1 = random.sample(faces, 3)
                            team2 = random.sample(heels, 3)
                            matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                            booked_workers.update([w[0] for w in team1 + team2])
                            continue
                    # Fallback
                    if len(pool) < 6:
                        continue
                    t1 = random.sample(pool, 3)
                    t2 = random.sample([w for w in pool if w not in t1], 3)
                    matches.append(([x[0] for x in t1], [x[0] for x in t2], mtype))
                    booked_workers.update([x[0] for x in t1 + t2])
                elif mtype == "4v4":
                    # Use stables if checked
                    if use_stables:
                        stable_teams = []
                        for s in stables:
                            members = [int(getattr(s, f'Member{i}')) for i in range(1, 11) if getattr(s, f'Member{i}', 0)]
                            members = [m for m in members if m in [w[0] for w in pool]]
                            if len(members) >= 4:
                                stable_teams.append(members)
                        random.shuffle(stable_teams)
                        used = set()
                        for t1 in stable_teams:
                            for t2 in stable_teams:
                                if t1 != t2 and not (set(t1[:4]) & set(t2[:4])) and len(t1) >= 4 and len(t2) >= 4:
                                    matches.append((t1[:4], t2[:4], mtype))
                                    booked_workers.update(t1[:4] + t2[:4])
                                    used.update(t1[:4] + t2[:4])
                                    break
                            if used:
                                break
                        if used:
                            continue
                    # Face/Heel logic
                    if use_faceheel:
                        faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                        heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                        if len(faces) >= 4 and len(heels) >= 4:
                            team1 = random.sample(faces, 4)
                            team2 = random.sample(heels, 4)
                            matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                            booked_workers.update([w[0] for w in team1 + team2])
                            continue
                    # Fallback
                    if len(pool) < 8:
                        continue
                    t1 = random.sample(pool, 4)
                    t2 = random.sample([w for w in pool if w not in t1], 4)
                    matches.append(([x[0] for x in t1], [x[0] for x in t2], mtype))
                    booked_workers.update([x[0] for x in t1 + t2])
                elif mtype == "5v5":
                    # Use stables if checked
                    if use_stables:
                        stable_teams = []
                        for s in stables:
                            members = [int(getattr(s, f'Member{i}')) for i in range(1, 11) if getattr(s, f'Member{i}', 0)]
                            members = [m for m in members if m in [w[0] for w in pool]]
                            if len(members) >= 5:
                                stable_teams.append(members)
                        random.shuffle(stable_teams)
                        used = set()
                        for t1 in stable_teams:
                            for t2 in stable_teams:
                                if t1 != t2 and not (set(t1[:5]) & set(t2[:5])) and len(t1) >= 5 and len(t2) >= 5:
                                    matches.append((t1[:5], t2[:5], mtype))
                                    booked_workers.update(t1[:5] + t2[:5])
                                    used.update(t1[:5] + t2[:5])
                                    break
                            if used:
                                break
                        if used:
                            continue
                    # Face/Heel logic
                    if use_faceheel:
                        faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                        heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                        if len(faces) >= 5 and len(heels) >= 5:
                            team1 = random.sample(faces, 5)
                            team2 = random.sample(heels, 5)
                            matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                            booked_workers.update([w[0] for w in team1 + team2])
                            continue
                    # Fallback
                    if len(pool) < 10:
                        continue
                    t1 = random.sample(pool, 5)
                    t2 = random.sample([w for w in pool if w not in t1], 5)
                    matches.append(([x[0] for x in t1], [x[0] for x in t2], mtype))
                    booked_workers.update([x[0] for x in t1 + t2])
        # Otherwise, use the provided matches (from the table)
        # Clear pre-booking
        cursor.execute('DELETE FROM tblPreBooking')
        cursor.execute('DELETE FROM tblPreBookingInvolvedMatch')
        cursor.execute('DELETE FROM tblPreBookingNote')
        self.conn.commit()
        # Insert pre-bookings for provided matches
        cursor.execute('SELECT MAX(UID) FROM tblPreBooking')
        last_prebooking_id = cursor.fetchone()[0] or 0
        for i, m in enumerate(matches):
            pb_uid = last_prebooking_id + i + 1
            card_uid = card_uids[i % len(card_uids)]
            mtype = m.get("type", "1v1")
            side1 = m.get("side1", [])
            side2 = m.get("side2", [])
            winner = m.get("winner", "")
            length = m.get("length", 10)
            match_uid = m.get("match_uid")
            # Build match name
            def side_display(side):
                return ", ".join([n for t, n, id_ in side])
            match_name = f"{side_display(side1)} vs {side_display(side2)}"
            # Insert into tblPreBooking
            cursor.execute("""
                INSERT INTO tblPreBooking (UID, Booking_Name, FedUID, CardUID, TVUID, Match, MatchUID, Length, Major, Belt1, Belt2, Belt3, Booked, AngleOutput, Scripted)
                VALUES (?, ?, ?, ?, 0, 1, ?, ?, 1, 0, 0, 0, 0, 0, NULL)
            """, (pb_uid, match_name, fed_uid, card_uid, match_uid, length))
            # Insert involved (just names, as IDs are not available in this UI)
            pos = 1
            for t, n, id_ in side1:
                cursor.execute("INSERT INTO tblPreBookingInvolvedMatch (PreBookingUID, FedUID, Position, Involved, Complain) VALUES (?, ?, ?, ?, 0)", (pb_uid, fed_uid, pos, int(id_)))
                pos += 1
            for t, n, id_ in side2:
                cursor.execute("INSERT INTO tblPreBookingInvolvedMatch (PreBookingUID, FedUID, Position, Involved, Complain) VALUES (?, ?, ?, ?, 0)", (pb_uid, fed_uid, pos, int(id_)))
                pos += 1
            
            all_participants = side1 + side2
            if all_participants:
                winner_uid = random.choice(all_participants)
                cursor.execute("""
                    INSERT INTO tblPreBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, 1, 200, 0, 0, 0, 0, 0, 0, 0, 1, ?, 0, 0, NULL)
                """, (pb_uid, fed_uid))
            print(winner)
            if winner == "Side 1" and side1:
                winner_uid = random.choice(side1)
                cursor.execute("""
                    INSERT INTO tblPreBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, 1, 1, ?, 0, 0, 0, 0, 0, 0, 1, ?, 0, 0, NULL)
                """, (pb_uid, int(winner_uid[2]), fed_uid))
            elif winner == "Side 2" and side2:
                winner_uid = random.choice(side2)
                cursor.execute("""
                    INSERT INTO tblPreBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, 1, 1, ?, 0, 0, 0, 0, 0, 0, 1, ?, 0, 0, NULL)
                """, (pb_uid, int(winner_uid[2]), fed_uid))
        self.conn.commit()
        # Transfer pre-booked to booked (as in func4_tab.py)
        cursor.execute("SELECT Announce1, Announce2, Announce3 FROM tblFed WHERE UID = ?", (fed_uid,))
        ann = cursor.fetchone()
        announcer1 = ann[0] if ann else None
        announcer2 = ann[1] if ann else None
        announcer3 = ann[2] if ann else None
        cursor.execute("SELECT WorkerUID FROM tblContract WHERE FedUID = ? AND Position_Referee = 1", (fed_uid,))
        referees = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT WorkerUID FROM tblContract WHERE FedUID = ? AND Position_Roadagent = 1", (fed_uid,))
        roadagents = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT MAX(Segment_Order) FROM tblUserBooking")
        max_order = cursor.fetchone()[0] or 0
        cursor.execute("SELECT MAX(UID) FROM tblUserBooking")
        max_uid = cursor.fetchone()[0] or 0
        cursor.execute("SELECT MAX(Position) FROM tblUserBookingNote")
        max_note_pos = cursor.fetchone()[0] or 0
        cursor.execute("SELECT * FROM tblPreBooking WHERE FedUID = ?", (fed_uid,))
        prebookings = cursor.fetchall()
        for i, pb in enumerate(prebookings):
            new_uid = max_uid + i + 1
            new_order = i + 1
            referee = random.choice(referees) if referees else None
            roadagent = random.choice(roadagents) if roadagents else None
            cursor.execute("""
                INSERT INTO tblUserBooking (
                    UID, Segment_Name, MainShow, PostShow, Segment_Order, Match, MatchUID, OverallRating, Referee, RoadAgent, Belt1, Belt2, Belt3, Announcer1, Announcer2, Announcer3, Length, Major, PreBookingUID, Completed, Problematic, ABFlag, ABRating, ABMin, ABMax, AngleOutput, Scripted
                )
                SELECT ?, Booking_Name, 1, 0, ?, Match, MatchUID, -1, ?, ?, Belt1, Belt2, Belt3, ?, ?, ?, Length, Major, 0, 0, 0, 0, NULL, NULL, NULL, AngleOutput, Scripted
                FROM tblPreBooking WHERE UID = ?
            """, (new_uid, new_order, referee, roadagent, announcer1, announcer2, announcer3, pb.UID))
            # Copy involved
            cursor.execute("SELECT * FROM tblPreBookingInvolvedMatch WHERE PreBookingUID = ?", (pb.UID,))
            for inv in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO tblUserBookingInvolvedMatch (UserBookingUID, FedUID, Position, Involved, Complain)
                    VALUES (?, ?, ?, ?, ?)
                """, (new_uid, inv.FedUID, inv.Position, inv.Involved, inv.Complain))
            # Copy notes
            cursor.execute("SELECT * FROM tblPreBookingNote WHERE UserBookingUID = ?", (pb.UID,))
            for note in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO tblUserBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_uid, note.Position, note.RoadAgent_Type, note.RoadAgent_Worker, note.RoadAgent_Attack, note.Used, note.BeltUID, note.Champion1, note.Champion2, note.Champion3, note.Match, note.FedUID, note.StoryUID, getattr(note, 'IdeaUID', None), getattr(note, 'IdeaName', None)
                ))
        # After copying, delete the pre-booked matches and related involved/note entries
        if prebookings:
            prebooking_uids = [pb.UID for pb in prebookings]
            qmarks = ','.join(['?'] * len(prebooking_uids))
            cursor.execute(f"DELETE FROM tblPreBookingInvolvedMatch WHERE PreBookingUID IN ({qmarks})", prebooking_uids)
            cursor.execute(f"DELETE FROM tblPreBookingNote WHERE UserBookingUID IN ({qmarks})", prebooking_uids)
            cursor.execute(f"DELETE FROM tblPreBooking WHERE UID IN ({qmarks})", prebooking_uids)
            self.conn.commit()
        self.conn.commit()
        self.status_label.config(text=f"Booked {len(matches)} matches.")
        messagebox.showinfo("Done", f"Booked {len(matches)} matches.")

    def move_match_up(self):
        """
        Move the selected match up in the match list and treeview.
        """
        sel = self.match_tree.selection()
        if not sel:
            return
        idx = self.match_tree.index(sel[0])
        if idx > 0:
            # Swap in matches list
            self.matches[idx - 1], self.matches[idx] = self.matches[idx], self.matches[idx - 1]
            # Swap in treeview
            above = self.match_tree.get_children()[idx - 1]
            vals = self.match_tree.item(sel[0], 'values')
            above_vals = self.match_tree.item(above, 'values')
            self.match_tree.item(sel[0], values=above_vals)
            self.match_tree.item(above, values=vals)
            self.match_tree.selection_set(above)

    def move_match_down(self):
        """
        Move the selected match down in the match list and treeview.
        """
        sel = self.match_tree.selection()
        if not sel:
            return
        idx = self.match_tree.index(sel[0])
        children = self.match_tree.get_children()
        if idx < len(children) - 1:
            # Swap in matches list
            self.matches[idx + 1], self.matches[idx] = self.matches[idx], self.matches[idx + 1]
            # Swap in treeview
            below = children[idx + 1]
            vals = self.match_tree.item(sel[0], 'values')
            below_vals = self.match_tree.item(below, 'values')
            self.match_tree.item(sel[0], values=below_vals)
            self.match_tree.item(below, values=vals)
            self.match_tree.selection_set(below)
