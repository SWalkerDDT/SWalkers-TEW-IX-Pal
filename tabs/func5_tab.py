import tkinter as tk
from tkinter import ttk, messagebox
import random
import pyodbc
from utils.round_robin import (
    clear_pre_booking,
)

class Func5Tab(ttk.Frame):
    """
    Auto Booker tab for booking a card with user-defined parameters.
    Provides UI for selecting promotion, match types, options, and times.
    Handles the logic for auto-booking matches and updating the database.
    """
    def __init__(self, parent, app):
        """
        Initialize the Auto Booker tab UI and variables.
        """
        super().__init__(parent)
        self.app = app
        self.conn = None
        self.feds = {}
        self.selected_fed = tk.StringVar()
        self.match_types_dict = {1: [], 2: [], 3: [], 4: [], 5: []}
        self.match_type_vars = {1: tk.StringVar(), 2: tk.StringVar(), 3: tk.StringVar(), 4: tk.StringVar(), 5: tk.StringVar()}
        self._build_ui()
        self.after(500, self.refresh)

    def _build_ui(self):
        """
        Build the user interface for the Auto Booker tab.
        """
        ttk.Label(self, text="Auto Booker for Tonight's Show").pack(pady=5)
        fed_frame = ttk.Frame(self)
        fed_frame.pack(pady=2)
        ttk.Label(fed_frame, text="User Promotion:").pack(side=tk.LEFT)
        self.fed_combo = ttk.Combobox(fed_frame, state="readonly", textvariable=self.selected_fed)
        self.fed_combo.pack(side=tk.LEFT, padx=5)
        self.fed_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        param_frame = ttk.LabelFrame(self, text="Match Type Percentages (must sum to 100%)")
        param_frame.pack(fill=tk.X, padx=5, pady=5)
        self.singles_var = tk.IntVar(value=10)
        self.tag_var = tk.IntVar(value=20)
        self.three_var = tk.IntVar(value=30)
        self.four_var = tk.IntVar(value=30)
        self.five_var = tk.IntVar(value=10)
        ttk.Label(param_frame, text="Singles %").grid(row=0, column=0)
        ttk.Entry(param_frame, textvariable=self.singles_var, width=5).grid(row=0, column=1)
        ttk.Label(param_frame, text="Tag %").grid(row=0, column=2)
        ttk.Entry(param_frame, textvariable=self.tag_var, width=5).grid(row=0, column=3)
        ttk.Label(param_frame, text="3v3 %").grid(row=0, column=4)
        ttk.Entry(param_frame, textvariable=self.three_var, width=5).grid(row=0, column=5)
        ttk.Label(param_frame, text="4v4 %").grid(row=0, column=6)
        ttk.Entry(param_frame, textvariable=self.four_var, width=5).grid(row=0, column=7)
        ttk.Label(param_frame, text="5v5 %").grid(row=0, column=8)
        ttk.Entry(param_frame, textvariable=self.five_var, width=5).grid(row=0, column=9)
        dropdown_frame = ttk.LabelFrame(self, text="Match Type for Each Kind")
        dropdown_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(dropdown_frame, text="Singles (1v1):").grid(row=0, column=0)
        self.singles_combo = ttk.Combobox(dropdown_frame, textvariable=self.match_type_vars[1], state="readonly")
        self.singles_combo.grid(row=0, column=1)
        ttk.Label(dropdown_frame, text="Tag (2v2):").grid(row=0, column=2)
        self.tag_combo = ttk.Combobox(dropdown_frame, textvariable=self.match_type_vars[2], state="readonly")
        self.tag_combo.grid(row=0, column=3)
        ttk.Label(dropdown_frame, text="3v3:").grid(row=0, column=4)
        self.three_combo = ttk.Combobox(dropdown_frame, textvariable=self.match_type_vars[3], state="readonly")
        self.three_combo.grid(row=0, column=5)
        ttk.Label(dropdown_frame, text="4v4:").grid(row=0, column=6)
        self.four_combo = ttk.Combobox(dropdown_frame, textvariable=self.match_type_vars[4], state="readonly")
        self.four_combo.grid(row=0, column=7)
        ttk.Label(dropdown_frame, text="5v5:").grid(row=0, column=8)
        self.five_combo = ttk.Combobox(dropdown_frame, textvariable=self.match_type_vars[5], state="readonly")
        self.five_combo.grid(row=0, column=9)
        opt_frame = ttk.LabelFrame(self, text="Options")
        opt_frame.pack(fill=tk.X, padx=5, pady=5)
        self.num_matches_var = tk.IntVar(value=7)
        self.use_stables_var = tk.BooleanVar(value=True)
        self.use_weight_var = tk.BooleanVar(value=True)
        self.use_faceheel_var = tk.BooleanVar(value=True)
        self.allow_intergender_var = tk.BooleanVar(value=True)
        ttk.Label(opt_frame, text="Number of Matches:").grid(row=0, column=0)
        ttk.Entry(opt_frame, textvariable=self.num_matches_var, width=5).grid(row=0, column=1)
        ttk.Checkbutton(opt_frame, text="Use Stables", variable=self.use_stables_var).grid(row=0, column=2)
        ttk.Checkbutton(opt_frame, text="Use Weight Limit", variable=self.use_weight_var).grid(row=0, column=3)
        ttk.Checkbutton(opt_frame, text="Use Face/Heel", variable=self.use_faceheel_var).grid(row=0, column=4)
        ttk.Checkbutton(opt_frame, text="Allow Intergender Matches", variable=self.allow_intergender_var).grid(row=0, column=5)
        time_frame = ttk.LabelFrame(self, text="Match Times (minutes)")
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        self.main_time_var = tk.IntVar(value=20)
        self.comain_time_var = tk.IntVar(value=17)
        self.other_min_var = tk.IntVar(value=8)
        self.other_max_var = tk.IntVar(value=15)
        ttk.Label(time_frame, text="Main Event:").grid(row=0, column=0)
        ttk.Entry(time_frame, textvariable=self.main_time_var, width=5).grid(row=0, column=1)
        ttk.Label(time_frame, text="Co-Main:").grid(row=0, column=2)
        ttk.Entry(time_frame, textvariable=self.comain_time_var, width=5).grid(row=0, column=3)
        ttk.Label(time_frame, text="Other Min:").grid(row=0, column=4)
        ttk.Entry(time_frame, textvariable=self.other_min_var, width=5).grid(row=0, column=5)
        ttk.Label(time_frame, text="Other Max:").grid(row=0, column=6)
        ttk.Entry(time_frame, textvariable=self.other_max_var, width=5).grid(row=0, column=7)
        ttk.Button(self, text="Auto Book Tonight's Show", command=self.auto_book).pack(pady=8)
        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(pady=2)

    def refresh(self):
        """
        Refresh the tab by reloading the current date, promotions, and match types from the database.
        """
        self.conn = self.app.conn
        if self.conn:
            self.load_current_date()
            self.load_feds()
            self.load_match_types()

    def load_current_date(self):
        """
        Load the current game date from the database.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT CurrentGameDate FROM tblGameInfo")
        row = cursor.fetchone()
        self.current_date = row[0] if row else None
        cursor.close()

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

    def load_match_types(self):
        """
        Load available match types for each kind (1v1, 2v2, etc.) from the database and update dropdowns.
        """
        cursor = self.conn.cursor()
        # 1v1
        cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = 1")
        self.match_types_dict[1] = [(row.UID, row.Name) for row in cursor.fetchall()]
        singles_names = [name for _, name in self.match_types_dict[1]]
        self.singles_combo['values'] = singles_names
        if singles_names:
            if self.match_type_vars[1].get() not in singles_names:
                self.match_type_vars[1].set(singles_names[0])
            self.singles_combo.set(self.match_type_vars[1].get())
        # 2v2
        cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = 2")
        self.match_types_dict[2] = [(row.UID, row.Name) for row in cursor.fetchall()]
        tag_names = [name for _, name in self.match_types_dict[2]]
        self.tag_combo['values'] = tag_names
        if tag_names:
            if self.match_type_vars[2].get() not in tag_names:
                self.match_type_vars[2].set(tag_names[0])
            self.tag_combo.set(self.match_type_vars[2].get())
        # 3v3
        cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = 3")
        self.match_types_dict[3] = [(row.UID, row.Name) for row in cursor.fetchall()]
        three_names = [name for _, name in self.match_types_dict[3]]
        self.three_combo['values'] = three_names
        if three_names:
            if self.match_type_vars[3].get() not in three_names:
                self.match_type_vars[3].set(three_names[0])
            self.three_combo.set(self.match_type_vars[3].get())
        # 4v4
        cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = 4")
        self.match_types_dict[4] = [(row.UID, row.Name) for row in cursor.fetchall()]
        four_names = [name for _, name in self.match_types_dict[4]]
        self.four_combo['values'] = four_names
        if four_names:
            if self.match_type_vars[4].get() not in four_names:
                self.match_type_vars[4].set(four_names[0])
            self.four_combo.set(self.match_type_vars[4].get())
        # 5v5
        cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = 5")
        self.match_types_dict[5] = [(row.UID, row.Name) for row in cursor.fetchall()]
        five_names = [name for _, name in self.match_types_dict[5]]
        self.five_combo['values'] = five_names
        if five_names:
            if self.match_type_vars[5].get() not in five_names:
                self.match_type_vars[5].set(five_names[0])
            self.five_combo.set(self.match_type_vars[5].get())
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

    def auto_book(self):
        """
        Automatically book matches for tonight's show based on user parameters and update the database.
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
        cursor.execute("SELECT tblContract.WorkerUID, tblContract.Face, tblWorker.Gender FROM tblContract INNER JOIN tblWorker ON tblContract.WorkerUID = tblWorker.UID WHERE tblContract.FedUID = ? AND tblContract.Position_Wrestler = 1", (fed_uid,))
        wrestlers = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        wrestler_ids = [w[0] for w in wrestlers]
        gender_map = {w[0]: w[2] for w in wrestlers}
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
        allow_intergender = self.allow_intergender_var.get()
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
            # Enforce gender if not intergender
            if not allow_intergender:
                gender_counts = {}
                for w in pool:
                    gender_counts[w[2]] = gender_counts.get(w[2], 0) + 1
                if gender_counts:
                    main_gender = max(gender_counts, key=gender_counts.get)
                    pool = [w for w in pool if w[2] == main_gender]
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
                if len(pool) < 2:
                    continue
                p1, p2 = random.sample(pool, 2)
                matches.append(([p1[0]], [p2[0]], mtype))
                booked_workers.update([p1[0], p2[0]])
            elif mtype == "tag":
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
                                # Gender restriction
                                if not allow_intergender and (len(set(gender_map.get(x) for x in t1[:2] + t2[:2])) > 1):
                                    continue
                                matches.append((t1[:2], t2[:2], mtype))
                                booked_workers.update(t1[:2] + t2[:2])
                                used.update(t1[:2] + t2[:2])
                                break
                        if used:
                            break
                    if used:
                        continue
                if use_faceheel:
                    faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                    heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                    if len(faces) >= 2 and len(heels) >= 2:
                        team1 = random.sample(faces, 2)
                        team2 = random.sample(heels, 2)
                        # Gender restriction
                        if not allow_intergender and (len(set(w[2] for w in team1 + team2)) > 1):
                            continue
                        matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                        booked_workers.update([w[0] for w in team1 + team2])
                        continue
                if len(pool) < 4:
                    continue
                # Gender restriction
                if not allow_intergender:
                    genders = set(w[2] for w in pool)
                    found = False
                    for g in genders:
                        same_gender = [w for w in pool if w[2] == g]
                        if len(same_gender) >= 4:
                            pool = same_gender
                            found = True
                            break
                    if not found:
                        continue
                team1 = random.sample(pool, 2)
                team2 = random.sample([w for w in pool if w not in team1], 2)
                matches.append(([team1[0][0], team1[1][0]], [team2[0][0], team2[1][0]], mtype))
                booked_workers.update([team1[0][0], team1[1][0], team2[0][0], team2[1][0]])
            elif mtype == "3v3":
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
                                if not allow_intergender and (len(set(gender_map.get(x) for x in t1[:3] + t2[:3])) > 1):
                                    continue
                                matches.append((t1[:3], t2[:3], mtype))
                                booked_workers.update(t1[:3] + t2[:3])
                                used.update(t1[:3] + t2[:3])
                                break
                        if used:
                            break
                    if used:
                        continue
                if use_faceheel:
                    faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                    heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                    if len(faces) >= 3 and len(heels) >= 3:
                        team1 = random.sample(faces, 3)
                        team2 = random.sample(heels, 3)
                        if not allow_intergender and (len(set(w[2] for w in team1 + team2)) > 1):
                            continue
                        matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                        booked_workers.update([w[0] for w in team1 + team2])
                        continue
                if len(pool) < 6:
                    continue
                if not allow_intergender:
                    genders = set(w[2] for w in pool)
                    found = False
                    for g in genders:
                        same_gender = [w for w in pool if w[2] == g]
                        if len(same_gender) >= 6:
                            pool = same_gender
                            found = True
                            break
                    if not found:
                        continue
                t1 = random.sample(pool, 3)
                t2 = random.sample([w for w in pool if w not in t1], 3)
                matches.append(([x[0] for x in t1], [x[0] for x in t2], mtype))
                booked_workers.update([x[0] for x in t1 + t2])
            elif mtype == "4v4":
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
                                if not allow_intergender and (len(set(gender_map.get(x) for x in t1[:4] + t2[:4])) > 1):
                                    continue
                                matches.append((t1[:4], t2[:4], mtype))
                                booked_workers.update(t1[:4] + t2[:4])
                                used.update(t1[:4] + t2[:4])
                                break
                        if used:
                            break
                    if used:
                        continue
                if use_faceheel:
                    faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                    heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                    if len(faces) >= 4 and len(heels) >= 4:
                        team1 = random.sample(faces, 4)
                        team2 = random.sample(heels, 4)
                        if not allow_intergender and (len(set(w[2] for w in team1 + team2)) > 1):
                            continue
                        matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                        booked_workers.update([w[0] for w in team1 + team2])
                        continue
                if len(pool) < 8:
                    continue
                if not allow_intergender:
                    genders = set(w[2] for w in pool)
                    found = False
                    for g in genders:
                        same_gender = [w for w in pool if w[2] == g]
                        if len(same_gender) >= 8:
                            pool = same_gender
                            found = True
                            break
                    if not found:
                        continue
                t1 = random.sample(pool, 4)
                t2 = random.sample([w for w in pool if w not in t1], 4)
                matches.append(([x[0] for x in t1], [x[0] for x in t2], mtype))
                booked_workers.update([x[0] for x in t1 + t2])
            elif mtype == "5v5":
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
                                if not allow_intergender and (len(set(gender_map.get(x) for x in t1[:5] + t2[:5])) > 1):
                                    continue
                                matches.append((t1[:5], t2[:5], mtype))
                                booked_workers.update(t1[:5] + t2[:5])
                                used.update(t1[:5] + t2[:5])
                                break
                        if used:
                            break
                    if used:
                        continue
                if use_faceheel:
                    faces = [w for w in pool if face_map.get(w[0], 1) == 1]
                    heels = [w for w in pool if face_map.get(w[0], 1) == 0]
                    if len(faces) >= 5 and len(heels) >= 5:
                        team1 = random.sample(faces, 5)
                        team2 = random.sample(heels, 5)
                        if not allow_intergender and (len(set(w[2] for w in team1 + team2)) > 1):
                            continue
                        matches.append(([w[0] for w in team1], [w[0] for w in team2], mtype))
                        booked_workers.update([w[0] for w in team1 + team2])
                        continue
                if len(pool) < 10:
                    continue
                if not allow_intergender:
                    genders = set(w[2] for w in pool)
                    found = False
                    for g in genders:
                        same_gender = [w for w in pool if w[2] == g]
                        if len(same_gender) >= 10:
                            pool = same_gender
                            found = True
                            break
                    if not found:
                        continue
                t1 = random.sample(pool, 5)
                t2 = random.sample([w for w in pool if w not in t1], 5)
                matches.append(([x[0] for x in t1], [x[0] for x in t2], mtype))
                booked_workers.update([x[0] for x in t1 + t2])
        # Sort matches by average perception (highest first)
        def avg_perception(match):
            side1, side2, _ = match
            all_ids = side1 + side2
            if not all_ids:
                return 0
            scores = [perceptions.get(uid, 50) for uid in all_ids]
            return sum(scores) / len(scores) if scores else 0
        matches.sort(key=avg_perception, reverse=True)
        #matches = matches[::-1]  # Invert order: least important first
        # Pre-book all matches
        def get_worker_names(uids):
            if not uids:
                return []
            batch_size = 50
            names = {}
            for i in range(0, len(uids), batch_size):
                batch = tuple(uids[i:i+batch_size])
                qmarks = ','.join(['?'] * len(batch))
                cursor.execute(f"SELECT UID, Name FROM tblWorker WHERE UID IN ({qmarks})", batch)
                for row in cursor.fetchall():
                    names[row[0]] = row[1]
            return names
        worker_names = get_worker_names(wrestler_ids)
        # Clear pre-booking
        cursor.execute('DELETE FROM tblPreBooking')
        cursor.execute('DELETE FROM tblPreBookingInvolvedMatch')
        cursor.execute('DELETE FROM tblPreBookingNote')
        self.conn.commit()
        # Insert pre-bookings
        cursor.execute('SELECT MAX(UID) FROM tblPreBooking')
        last_prebooking_id = cursor.fetchone()[0] or 0
        for i, (side1, side2, mtype) in enumerate(matches):
            pb_uid = last_prebooking_id + i + 1
            card_uid = card_uids[i % len(card_uids)]
            # Build match name
            def get_names(uids):
                return [worker_names.get(uid, str(uid)) for uid in uids]
            if mtype == "singles":
                match_name = f"{get_names(side1)[0]} vs {get_names(side2)[0]}"
            else:
                match_name = f"{'/'.join(get_names(side1))} vs {'/'.join(get_names(side2))}"
            # Pick match_uid from dropdown
            if mtype == "singles":
                match_uid = next((uid for uid, name in self.match_types_dict[1] if name == self.match_type_vars[1].get()), None)
            elif mtype == "tag":
                match_uid = next((uid for uid, name in self.match_types_dict[2] if name == self.match_type_vars[2].get()), None)
            elif mtype == "3v3":
                match_uid = next((uid for uid, name in self.match_types_dict[3] if name == self.match_type_vars[3].get()), None)
            elif mtype == "4v4":
                match_uid = next((uid for uid, name in self.match_types_dict[4] if name == self.match_type_vars[4].get()), None)
            elif mtype == "5v5":
                match_uid = next((uid for uid, name in self.match_types_dict[5] if name == self.match_type_vars[5].get()), None)
            else:
                match_uid = None
            # Set match length: last match is main, second to last is co-main
            if i == len(matches) - 1:
                length = self.main_time_var.get()
            elif i == len(matches) - 2:
                length = self.comain_time_var.get()
            else:
                length = random.randint(self.other_min_var.get(), self.other_max_var.get())
            # Insert into tblPreBooking
            cursor.execute("""
                INSERT INTO tblPreBooking (UID, Booking_Name, FedUID, CardUID, TVUID, Match, MatchUID, Length, Major, Belt1, Belt2, Belt3, Booked, AngleOutput, Scripted)
                VALUES (?, ?, ?, ?, 0, 1, ?, ?, 1, 0, 0, 0, 0, 0, NULL)
            """, (pb_uid, match_name, fed_uid, card_uid, match_uid, length))
            # Insert involved
            pos = 1
            for w in side1:
                cursor.execute("INSERT INTO tblPreBookingInvolvedMatch (PreBookingUID, FedUID, Position, Involved, Complain) VALUES (?, ?, ?, ?, 0)", (pb_uid, fed_uid, pos, w))
                pos += 1
            for w in side2:
                cursor.execute("INSERT INTO tblPreBookingInvolvedMatch (PreBookingUID, FedUID, Position, Involved, Complain) VALUES (?, ?, ?, ?, 0)", (pb_uid, fed_uid, pos, w))
                pos += 1
            # Insert note (winner random)
            all_participants = side1 + side2
            if all_participants:
                winner_uid = random.choice(all_participants)
                cursor.execute("""
                    INSERT INTO tblPreBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, 1, 200, 0, 0, 0, 0, 0, 0, 0, 1, ?, 0, 0, NULL)
                """, (pb_uid, fed_uid))
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
            new_order = i + 1  # Main event is position 1
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
            # Build qmarks for parameterized IN clause
            qmarks = ','.join(['?'] * len(prebooking_uids))
            cursor.execute(f"DELETE FROM tblPreBookingInvolvedMatch WHERE PreBookingUID IN ({qmarks})", prebooking_uids)
            cursor.execute(f"DELETE FROM tblPreBookingNote WHERE UserBookingUID IN ({qmarks})", prebooking_uids)
            cursor.execute(f"DELETE FROM tblPreBooking WHERE UID IN ({qmarks})", prebooking_uids)
            self.conn.commit()
        self.conn.commit()
        
        self.status_label.config(text=f"Auto booked {len(matches)} matches for tonight's show(s).")
        messagebox.showinfo("Done", f"Auto booked {len(matches)} matches for tonight's show(s).")
