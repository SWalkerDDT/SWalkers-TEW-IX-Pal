import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import random

class Func4Tab(ttk.Frame):
    """
    Tab for copying selected prebooked matches from a card to the user booked card in the savegame.
    Only user-controlled promotions are shown. User can select which matches to book.
    """
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.conn = None
        self.current_date = None
        self.feds = {}
        self.selected_fed = tk.StringVar()
        self.show_uids = []
        self.prebookings = []
        self.match_vars = []

        # Sidebar
        sidebar_frame = ttk.Frame(self)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ttk.Label(
            sidebar_frame,
            text="""This is the prebook to user booking automation tab.
            \n\nFirst choose your current promotion your are running from the dropdown and make sure, there is a show running on the current day and you are after the pre show phase!
            \n\nYou see a list of all prebooked matches for tonight's shows. You can select which ones you want to copy to the user booked card. You can also select a winner for each match.
            \n\nPress 'Book' to copy the selected matches to the user booked card. The matches will be added at the end of the card.
            """,
            wraplength=180,
            justify="left"
        ).pack(anchor="n", fill=tk.X, pady=10)

        # UI
        ttk.Label(self, text="Copy Prebooked Matches to User Booked Card").pack(pady=5)
        self.date_label = ttk.Label(self, text="Current Date: ...")
        self.date_label.pack(pady=2)
        fed_frame = ttk.Frame(self)
        fed_frame.pack(pady=2)
        ttk.Label(fed_frame, text="User Promotion:").pack(side=tk.LEFT)
        self.fed_combo = ttk.Combobox(fed_frame, state="readonly", textvariable=self.selected_fed)
        self.fed_combo.pack(side=tk.LEFT, padx=5)
        self.fed_combo.bind("<<ComboboxSelected>>", lambda e: self.load_tonight_cards())
        ttk.Button(self, text="Refresh", command=self.refresh_tab).pack(pady=2)
        self.matches_frame = ttk.Frame(self)
        self.matches_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.winner_vars = []  
        self.length_vars = []  
        self.segment_orders = [] 
        btns_frame = ttk.Frame(self)
        btns_frame.pack(pady=2)
        ttk.Button(btns_frame, text="Check All", command=self.check_all_matches).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns_frame, text="Book", command=self.book_prebooked).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(pady=2)
        self.after(500, self.try_load)

       

    def try_load(self):
        self.conn = self.app.conn
        if self.conn:
            self.load_current_date()
            self.load_feds()

    def load_current_date(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT CurrentGameDate FROM tblGameInfo")
        row = cursor.fetchone()
        self.current_date = row[0] if row else None
        self.date_label.config(text=f"Current Date: {self.current_date}")
        cursor.close()

    def load_feds(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT UID, Name FROM tblFed WHERE User_Controlled = 1")
        self.feds = {str(row.UID): row.Name for row in cursor.fetchall()}
        self.fed_combo['values'] = list(self.feds.values())
        if self.feds:
            self.fed_combo.current(0)
            self.selected_fed.set(self.fed_combo.get())
            self.load_tonight_cards()
        else:
            self.selected_fed.set("")
            self.fed_combo.set("")
        cursor.close()

    def get_selected_fed_uid(self):
        name = self.selected_fed.get()
        for uid, n in self.feds.items():
            if n == name:
                return int(uid)
        return None

    def load_tonight_cards(self):
        for widget in self.matches_frame.winfo_children():
            widget.destroy()
        self.show_uids = []
        self.prebookings = []
        self.match_vars = []
        self.winner_vars = []
        self.length_vars = []
        self.segment_orders = []
        fed_uid = self.get_selected_fed_uid()
        if not fed_uid or not self.conn:
            return
        cursor = self.conn.cursor()
        # Get CardUIDs for tonight's user booked shows
        cursor.execute("SELECT CardUID FROM tblTonightsSchedule WHERE FedUID = ?", (fed_uid,))
        card_uids = [row[0] for row in cursor.fetchall()]
        if not card_uids:
            ttk.Label(self.matches_frame, text="No user booked shows for this promotion tonight.").pack()
            return
        self.show_uids = card_uids
        # Table header
        header = ttk.Frame(self.matches_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Select", width=6).pack(side=tk.LEFT)
        ttk.Label(header, text="Match Name", width=40).pack(side=tk.LEFT)
        ttk.Label(header, text="CardUID", width=10).pack(side=tk.LEFT)
        ttk.Label(header, text="Winner", width=20).pack(side=tk.LEFT)
        ttk.Label(header, text="Length", width=8).pack(side=tk.LEFT)
        ttk.Label(header, text="Segment Order", width=18).pack(side=tk.LEFT)
        # Treeview for matches
        columns = ("Select", "Match Name", "CardUID", "Winner", "Length", "Segment Order")
        self.match_tree = ttk.Treeview(self.matches_frame, columns=columns, show="headings", selectmode="none", height=12)
        for col in columns:
            self.match_tree.heading(col, text=col)
            self.match_tree.column(col, width=120 if col != "Match Name" else 260, anchor='center')
        self.match_tree.pack(fill=tk.BOTH, expand=True)
        self.match_tree.bind('<ButtonPress-1>', self._on_tree_drag_start)
        self.match_tree.bind('<B1-Motion>', self._on_tree_drag_motion)
        self.match_tree.bind('<ButtonRelease-1>', self._on_tree_drag_release)
        self.match_tree.bind('<Double-1>', self._on_tree_double_click)
        self._tree_drag_data = {'item': None, 'y': 0}
        self.tree_match_vars = []  
        # Query prebooked matches for all CardUIDs
        for card_uid in card_uids:
            cursor.execute("SELECT * FROM tblPreBooking WHERE CardUID = ?", (card_uid,))
            for pb in cursor.fetchall():
                self.prebookings.append(pb)
        if not self.prebookings:
            ttk.Label(self.matches_frame, text="No prebooked matches found for tonight's shows.").pack()
            return
        for idx, pb in enumerate(self.prebookings):
            select_var = tk.BooleanVar(value=False)
            winner_var = tk.StringVar()
            length_var = tk.StringVar(value=str(getattr(pb, 'Length', 10)))
            cursor2 = self.conn.cursor()
            cursor2.execute("SELECT Involved FROM tblPreBookingInvolvedMatch WHERE PreBookingUID = ?", (pb.UID,))
            winner_options = [str(row[0]) for row in cursor2.fetchall()]
            cursor2.close()
            self.tree_match_vars.append((select_var, pb, winner_var, length_var, winner_options))
            self.match_tree.insert("", "end", iid=str(idx), values=("", getattr(pb, 'Booking_Name', ''), getattr(pb, 'CardUID', ''), '', length_var.get(), idx+1))
        self._update_tree_segment_orders()

    def _on_tree_drag_start(self, event):
        item = self.match_tree.identify_row(event.y)
        if item:
            self._tree_drag_data['item'] = item
            self._tree_drag_data['y'] = event.y

    def _on_tree_drag_motion(self, event):
        item = self._tree_drag_data['item']
        if not item:
            return
        y = event.y
        above = self.match_tree.identify_row(y)
        if above and above != item:
            idx1 = self.match_tree.index(item)
            idx2 = self.match_tree.index(above)
            self.match_tree.move(item, '', idx2)
            # Move in internal list as well
            self.tree_match_vars.insert(idx2, self.tree_match_vars.pop(idx1))
            self._update_tree_segment_orders()

    def _on_tree_drag_release(self, event):
        self._tree_drag_data = {'item': None, 'y': 0}

    def _update_tree_segment_orders(self):
        for idx, item in enumerate(self.match_tree.get_children()):
            self.match_tree.set(item, "Segment Order", idx+1)

    def _on_tree_double_click(self, event):
        col = self.match_tree.identify_column(event.x)
        row = self.match_tree.identify_row(event.y)
        if not row or not col:
            return
        col_idx = int(col.replace('#', '')) - 1
        columns = ("Select", "Match Name", "CardUID", "Winner", "Length", "Segment Order")
        col_name = columns[col_idx]
        idx = int(row)
        select_var, pb, winner_var, length_var, winner_options = self.tree_match_vars[idx]
        if col_name == "Select":
            select_var.set(not select_var.get())
            self.match_tree.set(row, "Select", "✔" if select_var.get() else "")
        elif col_name == "Winner":
            combo = ttk.Combobox(self.match_tree, values=winner_options, textvariable=winner_var, state="readonly")
            x, y, width, height = self.match_tree.bbox(row, col)
            combo.place(x=x, y=y, width=width, height=height)
            combo.set(self.match_tree.set(row, "Winner"))
            combo.focus()
            def on_select(event=None):
                self.match_tree.set(row, "Winner", combo.get())
                combo.destroy()
            combo.bind('<<ComboboxSelected>>', on_select)
            combo.bind('<FocusOut>', lambda e: combo.destroy())
            combo.bind('<Return>', on_select)
        elif col_name == "Length":
            entry = ttk.Entry(self.match_tree, textvariable=length_var)
            x, y, width, height = self.match_tree.bbox(row, col)
            entry.place(x=x, y=y, width=width, height=height)
            entry.focus()
            def on_entry(event=None):
                self.match_tree.set(row, "Length", length_var.get())
                entry.destroy()
            entry.bind('<Return>', on_entry)
            entry.bind('<FocusOut>', lambda e: entry.destroy())

    def check_all_matches(self):
        for select_var, *_ in self.tree_match_vars:
            select_var.set(True)
            idx = self.tree_match_vars.index((select_var, *_))
            self.match_tree.set(str(idx), "Select", "✔")

    def book_prebooked(self):
        if not self.conn:
            messagebox.showerror("Error", "No database connection.")
            return
        fed_uid = self.get_selected_fed_uid()
        if not fed_uid:
            messagebox.showerror("Error", "No promotion selected.")
            return
        cursor = self.conn.cursor()
        # Get announcers from tblFed
        cursor.execute("SELECT Announce1, Announce2, Announce3 FROM tblFed WHERE UID = ?", (fed_uid,))
        ann = cursor.fetchone()
        announcer1 = ann[0] if ann else None
        announcer2 = ann[1] if ann else None
        announcer3 = ann[2] if ann else None
        # Get possible referees and road agents from tblContract
        cursor.execute("SELECT WorkerUID FROM tblContract WHERE FedUID = ? AND Position_Referee = 1", (fed_uid,))
        referees = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT WorkerUID FROM tblContract WHERE FedUID = ? AND Position_Roadagent = 1", (fed_uid,))
        roadagents = [row[0] for row in cursor.fetchall()]
        # 1. Only book checked matches (use current order and lengths)
        selected = []
        for idx, (select_var, pb, winner_var, length_var, _) in enumerate(self.tree_match_vars):
            if select_var.get():
                seg_order = int(self.match_tree.set(str(idx), "Segment Order"))
                selected.append((pb, winner_var.get(), length_var.get(), seg_order))
        if not selected:
            messagebox.showinfo("No Selection", "No matches selected.")
            return
        # 2. Get current max Segment_Order and UID in tblUserBooking
        cursor.execute("SELECT MAX(Segment_Order) FROM tblUserBooking")
        max_order = cursor.fetchone()[0] or 0
        cursor.execute("SELECT MAX(UID) FROM tblUserBooking")
        max_uid = cursor.fetchone()[0] or 0
        # 3. Get current max Position in tblUserBookingNote
        cursor.execute("SELECT MAX(Position) FROM tblUserBookingNote")
        max_note_pos = cursor.fetchone()[0] or 0
        # 4. Copy each selected prebooking to tblUserBooking and related tables
        for i, (pb, winner_uid, match_length, seg_order) in enumerate(selected):
            new_uid = max_uid + i + 1
            referee = random.choice(referees) if referees else None
            roadagent = random.choice(roadagents) if roadagents else None
            cursor.execute("""
                INSERT INTO tblUserBooking (
                    UID, Segment_Name, MainShow, PostShow, Segment_Order, Match, MatchUID, OverallRating, Referee, RoadAgent, Belt1, Belt2, Belt3, Announcer1, Announcer2, Announcer3, Length, Major, PreBookingUID, Completed, Problematic, ABFlag, ABRating, ABMin, ABMax, AngleOutput, Scripted
                )
                SELECT ?, Booking_Name, 1, 0, ?, Match, MatchUID, -1, ?, ?, Belt1, Belt2, Belt3, ?, ?, ?, ?, Major, UID, 0, 0, 0, NULL, NULL, NULL, AngleOutput, Scripted
                FROM tblPreBooking WHERE UID = ?
            """, (new_uid, i + 1 + max_order, referee, roadagent, announcer1, announcer2, announcer3, int(match_length), pb.UID))
            # Copy involved
            cursor.execute("SELECT * FROM tblPreBookingInvolvedMatch WHERE PreBookingUID = ?", (pb.UID,))
            for inv in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO tblUserBookingInvolvedMatch (UserBookingUID, FedUID, Position, Involved, Complain)
                    VALUES (?, ?, ?, ?, ?)
                """, (new_uid, inv.FedUID, inv.Position, inv.Involved, inv.Complain))
            cursor.execute("SELECT * FROM tblPreBookingNote WHERE UserBookingUID = ?", (pb.UID,))
            for note in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO tblUserBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_uid, note.Position, note.RoadAgent_Type, note.RoadAgent_Worker, note.RoadAgent_Attack, note.Used, note.BeltUID, note.Champion1, note.Champion2, note.Champion3, note.Match, note.FedUID, note.StoryUID, getattr(note, 'IdeaUID', None), getattr(note, 'IdeaName', None)
                ))
            if winner_uid:
                max_note_pos += 1
                cursor.execute("""
                    INSERT INTO tblUserBookingNote (
                        UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID, IdeaUID, IdeaName
                    ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 1, ?, 0, NULL, NULL)
                """, (
                    new_uid, max_note_pos, 1, int(winner_uid), fed_uid
                ))
        self.conn.commit()
        self.status_label.config(text=f"Copied {len(selected)} prebooked matches to user booking.")
        messagebox.showinfo("Done", f"Copied {len(selected)} prebooked matches to user booking.")

    def refresh_tab(self):
        """
        Refresh the current date and promotions from the connected MDB and update UI fields.
        """
        self.conn = self.app.conn
        if self.conn:
            self.load_current_date()
            self.load_feds()
            if self.feds:
                self.fed_combo.current(0)
                self.selected_fed.set(self.fed_combo.get())
                self.load_tonight_cards()
            else:
                self.selected_fed.set("")
                self.fed_combo.set("")
                for widget in self.matches_frame.winfo_children():
                    widget.destroy()
