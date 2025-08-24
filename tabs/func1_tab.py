import tkinter as tk
from tkinter import ttk, messagebox
import json 
from utils.round_robin import (
    clear_pre_booking,
    query_tournaments,
    query_tournament_participants,
    query_shows_of_fed,
    generate_round_robin_tournament,
    query_worker_name_by_id
)
from utils.round_robin import book_tournament as backend_book_tournament

class Func1Tab(ttk.Frame):
    """
    Round Robin Generator tab for managing tournaments, participants, and booking.
    Provides UI and logic for selecting tournaments, generating pairings, and booking matches.
    """
    def __init__(self, parent, app):
        """
        Initialize the Round Robin Generator tab UI and widgets.
        """
        super().__init__(parent)
        self.app = app
        self.conn = None
        self.tournaments = {}
        self.fed_id = None
        self.tournament_type = None
        self.participants = []  # list of tuples (worker_id, worker_name)
        self.schedule = []
        self.shows = {}  # {show_id: show_name}

        # Sidebar
        sidebar_frame = ttk.Frame(self)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ttk.Label(
            sidebar_frame,
            text="""This tab allows you to generate and book round-robin tournaments.
            \n\nFirst clear the booking if needed! 
            \n\n1)  Select a tournament from the dropdown and load its participants.
            \n\n2)  Match type gets auto-selected based on the tournament type (Single/Tag/Trios). You can choose a different match if needed. 
            \n\n3)  Participants can be reordered by dragging them in the list. 
            \n\n4)  Choose a prefix for match names (max 8 characters). 
            \n\n5)  Click 'Generate Pairings' to create a round-robin schedule. 
            \n\n6)  Assign shows from the dropdown and match lengths to each match in the schedule. 
            \n\n7)  Matches can be reordered by dragging them in the schedule list. 
            \n\n8)  Finally, click 'Book Tournament' to save everything to the database. 
            \n\n If there are any errors occuring during booking, you can choose to clear the pre-booking first and try again.
            """,
            wraplength=180,
            justify="left"
        ).pack(anchor="n", fill=tk.X, pady=10)

        # --- Step 0: Clear pre-booking ---
        clear_frame = ttk.Frame(self)
        clear_frame.pack(fill=tk.X, pady=5)
        self.clear_var = tk.BooleanVar()
        ttk.Checkbutton(clear_frame, text="Clear Pre-Booking", variable=self.clear_var).pack(side=tk.LEFT)
        ttk.Button(clear_frame, text="Apply", command=self.clear_prebooking).pack(side=tk.LEFT, padx=5)

        # --- Step 1: Tournament selection ---
        tourney_frame = ttk.Frame(self)
        tourney_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tourney_frame, text="Select Tournament:").pack(side=tk.LEFT)
        self.tourney_combo = ttk.Combobox(tourney_frame, state="readonly")
        self.tourney_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(tourney_frame, text="Load", command=self.load_tournament).pack(side=tk.LEFT, padx=5)

        # --- Step 2: Match type selection ---
        match_frame = ttk.Frame(self)
        match_frame.pack(fill=tk.X, pady=5)
        ttk.Label(match_frame, text="Select Match:").pack(side=tk.LEFT)

        self.match_var = tk.StringVar()
        self.match_combo = ttk.Combobox(match_frame, textvariable=self.match_var, state="readonly")
        self.match_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(match_frame, text="Load Matches", command=self.load_matches).pack(side=tk.LEFT, padx=5)

        # --- Step 3: Participants ---
        ttk.Label(self, text="Participants (drag to reorder):").pack()
        self.participant_tree = ttk.Treeview(self, columns=["Name"], show="headings", height=6)
        self.participant_tree.heading("Name", text="Participant")
        self.participant_tree.pack(fill=tk.X, padx=5, pady=5)
        self.enable_drag_and_drop(self.participant_tree)

        # --- Step 4: Prefix Entry ---
        prefix_frame = ttk.Frame(self)
        prefix_frame.pack(fill=tk.X, pady=5)
        ttk.Label(prefix_frame, text="Match Prefix (max 8 chars):").pack(side=tk.LEFT)
        self.prefix_var = tk.StringVar()
        ttk.Entry(prefix_frame, textvariable=self.prefix_var, width=10).pack(side=tk.LEFT, padx=5)

        # --- Step 5: Combined Schedule + Shows + Length ---
        ttk.Label(self, text="Schedule with Shows & Match Length (drag to reorder):").pack()
        self.combined_tree = ttk.Treeview(self, columns=["Day", "Match", "Show", "Length"], show="headings", height=10)
        for col in ["Day", "Match", "Show", "Length"]:
            self.combined_tree.heading(col, text=col)
        self.combined_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.enable_drag_and_drop(self.combined_tree)

        # --- Step 6: Generate pairings button ---
        ttk.Button(self, text="Generate Pairings", command=self.generate_pairings).pack(pady=5)

        # --- Step 7: Book tournament button ---
        ttk.Button(self, text="Book Tournament", command=self.on_book_tournament).pack(pady=10)

    # ---------------- Methods ----------------

    def clear_prebooking(self):
        """
        Clear pre-booking in the database if enabled.
        """
        if self.conn and self.clear_var.get():
            clear_pre_booking(self.conn)
            messagebox.showinfo("Done", "Pre-booking cleared!")

    def load_tournaments(self):
        """
        Load tournaments from the database and populate the dropdown.
        """
        if not self.conn:
            return
        self.tournaments, self.fed_id = query_tournaments(self.conn)
        self.tourney_combo["values"] = [f"{tid}: {val[0]}" for tid, val in self.tournaments.items()]
        self.shows = query_shows_of_fed(self.conn, self.fed_id)

    def load_tournament(self):
        """
        Load the selected tournament and its participants.
        Clears the participant and combined schedule trees and destroys any widgets in the combined tree.
        """
        sel = self.tourney_combo.get()
        if not sel:
            return
        # Destroy all child widgets in combined_tree (e.g., dropdowns, spinboxes)
        for child in self.combined_tree.winfo_children():
            child.destroy()
        # Clear trees on new tournament load
        self.participant_tree.delete(*self.participant_tree.get_children())
        self.combined_tree.delete(*self.combined_tree.get_children())
        tourney_id = int(sel.split(":")[0])
        self.tournament_type = self.tournaments[tourney_id][1]

        participant_ids = query_tournament_participants(self.conn, tourney_id, self.tournament_type)

        self.participants.clear()

        if self.tournament_type == 1:  # Singles
            self.participants = [(pid, query_worker_name_by_id(self.conn, pid)) for pid in participant_ids]
        else:  # Tag or Trios
            # Flatten teams into names for display
            for team in participant_ids:
                team_names = [query_worker_name_by_id(self.conn, pid) for pid in team]
                # store as (team_ids, "Name1|Name2|...")
                self.participants.append((team, "|".join(team_names)))

        # Populate tree
        for ids, name in self.participants:
            self.participant_tree.insert("", tk.END, values=[name], tags=(str(ids),))
        self.load_matches()

    def load_matches(self):
        """
        Load matches from tblMatch filtered by tournament type.
        """
        if not self.conn or not self.tournament_type:
            return

        cursor = self.conn.cursor()
        try:
            # tblTournament.Type gives tournament_type: 1,2,3
            # tblMatch.Match_Type should match
            cursor.execute("SELECT UID, Name FROM tblMatch WHERE Match_Type = ?", (self.tournament_type,))
            rows = cursor.fetchall()
            self.match_options = {row.UID: row.Name for row in rows}
            self.match_combo["values"] = list(self.match_options.values())
            if rows:
                self.match_combo.current(0)
        finally:
            cursor.close()

        
    def generate_pairings(self):
        """
        Generate round-robin pairings for the selected tournament and participants.
        """
        # Get participant IDs and names from the tree
        items = [(self.participant_tree.item(i, "tags")[0],
                self.participant_tree.item(i, "values")[0])
                for i in self.participant_tree.get_children()]

        # Map display names
        id_to_name = {}
        for tag, name in items:
            try:
                parsed = json.loads(tag)
            except:
                parsed = tag
            print(parsed)
            if isinstance(parsed, int):
                # Singles: just one participant
                id_to_name[parsed] = name
            elif isinstance(parsed, list) and all(isinstance(x, int) for x in parsed):
                # Tag/Trios: flat list of ints
                for pid in parsed:
                    id_to_name[pid] = name
            else:
                # Teams: nested lists
                def flatten(lst):
                    for i in lst:
                        if isinstance(i, list):
                            yield from flatten(i)
                        else:
                            yield i
                for pid in flatten(parsed):
                    id_to_name[pid] = name

        # Generate round-robin schedule
        if self.tournament_type == 1:
            participant_ids = [json.loads(tag) for tag, _ in items]
            # For singles, participant_ids is a list of ints, not lists
            if all(isinstance(pid, int) for pid in participant_ids):
                self.schedule = generate_round_robin_tournament(participant_ids)
            else:
                # Defensive: flatten if needed (shouldn't happen for singles)
                participant_ids = [p for sub in participant_ids for p in (sub if isinstance(sub, list) else [sub])]
                self.schedule = generate_round_robin_tournament(participant_ids)
        else:
            # Tag/Trios: use team IDs directly
            self.schedule = generate_round_robin_tournament([json.loads(tag) for tag, _ in items])
        
        # Clear combined tree
        self.combined_tree.delete(*self.combined_tree.get_children())

        # Insert matches
        for day, matches in enumerate(self.schedule, start=1):
            for m in matches:
                # Skip 'bye' if present
                if 'bye' in m:
                    continue
                # Build match string
                if self.tournament_type == 1:
                    match_str = f"{id_to_name[m[0]]} vs {id_to_name[m[1]]}"
                else:
                    team_names = ["|".join(id_to_name[pid] for pid in team) for team in m]
                    match_str = f"{team_names[0]} vs {team_names[1]}"
                # Store IDs as JSON in tag
                tag_value = json.dumps(m)
                item_id = self.combined_tree.insert("", tk.END, values=(day, match_str, "", 10), tags=(tag_value,))
                self.add_show_and_length_widgets(item_id)

    # ---------------- Widgets for Show + Length ----------------
    def add_show_and_length_widgets(self, item_id):
        """
        Add widgets for selecting show and match length for each scheduled match.
        """
        def place_widgets():
            bbox_show = self.combined_tree.bbox(item_id, column="Show")
            bbox_length = self.combined_tree.bbox(item_id, column="Length")
            if not bbox_show or not bbox_length:
                self.combined_tree.after(50, place_widgets)
                return

            # Show Combobox
            combo = ttk.Combobox(self.combined_tree, values=list(self.shows.values()), state="readonly")
            combo.place(x=bbox_show[0], y=bbox_show[1], width=bbox_show[2], height=bbox_show[3])
            combo.bind("<<ComboboxSelected>>", lambda e: self.combined_tree.set(item_id, "Show", combo.get()))

            # Match Length Spinbox
            spin = tk.Spinbox(self.combined_tree, from_=1, to=300, width=5)
            spin.place(x=bbox_length[0], y=bbox_length[1], width=bbox_length[2], height=bbox_length[3])
            spin.bind("<FocusOut>", lambda e: self.combined_tree.set(item_id, "Length", spin.get()))

        self.combined_tree.after(50, place_widgets)

    # ---------------- Book Tournament ----------------
    def on_book_tournament(self):
        """
        Book the tournament using the current schedule and user selections.
        """
        prefix = self.prefix_var.get()[:8]
        if not prefix:
            messagebox.showerror("Error", "Please enter a prefix for matches!")
            return

        rows = [self.combined_tree.item(i, "values") for i in self.combined_tree.get_children()]
        if not rows:
            messagebox.showerror("Error", "No matches to book!")
            return

        show_names = [r[2] for r in rows]
        lengths = [int(r[3]) if r[3] else 0 for r in rows]

        if "" in show_names:
            messagebox.showerror("Error", "Please assign shows to all matches!")
            return
        if any(l <= 0 for l in lengths):
            messagebox.showerror("Error", "Please set a valid match length for each match!")
            return

        # Map show names to IDs
        show_order = []
        for sname in show_names:
            for sid, name in self.shows.items():
                if name == sname:
                    show_order.append(sid)
                    break

        # Build schedule and match lengths dict
        sched_dict = {}
        match_lengths_dict = {}
        for idx, i in enumerate(self.combined_tree.get_children()):
            r = self.combined_tree.item(i, "values")
            day = int(r[0])
            match_tag = self.combined_tree.item(i, "tags")[0]

            try:
                match = json.loads(match_tag)
            except Exception:
                messagebox.showerror("Error", f"Invalid match tag: {match_tag}")
                return

            if day not in sched_dict:
                sched_dict[day] = []
                match_lengths_dict[day] = []

            # Singles as tuple, teams as list
            if self.tournament_type == 1:
                sched_dict[day].append(tuple(match))
            else:
                sched_dict[day].append(match)

            match_lengths_dict[day].append(lengths[idx])

        # Get selected match UID
        match_name = self.match_var.get()
        match_uid = None
        for uid, name in self.match_options.items():
            if name == match_name:
                match_uid = uid
                break

        if match_uid is None:
            messagebox.showerror("Error", "Please select a match!")
            return

        # Call backend
        backend_book_tournament(
            self.conn,
            prefix,
            sched_dict,
            show_order,
            match_lengths_dict,
            self.tournament_type,
            self.fed_id,
            match_uid=match_uid  # NEW
        )
        messagebox.showinfo("Success", "Tournament booked successfully!")

    # ---------------- Drag & Drop ----------------
    def enable_drag_and_drop(self, tree):
        """
        Enable drag-and-drop reordering for the given treeview widget.
        """
        def on_drag_start(event):
            self.drag_item = tree.identify_row(event.y)

        def on_drag_motion(event):
            row_under = tree.identify_row(event.y)
            if self.drag_item and row_under and row_under != self.drag_item:
                tree.move(self.drag_item, tree.parent(row_under), tree.index(row_under))

        tree.bind("<ButtonPress-1>", on_drag_start)
        tree.bind("<B1-Motion>", on_drag_motion)
