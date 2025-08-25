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
        self.winner_vars = []  # (tk.StringVar, pb, winner_options)
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
        # Query prebooked matches for all CardUIDs
        for card_uid in card_uids:
            cursor.execute("SELECT * FROM tblPreBooking WHERE CardUID = ?", (card_uid,))
            for pb in cursor.fetchall():
                self.prebookings.append(pb)
        if not self.prebookings:
            ttk.Label(self.matches_frame, text="No prebooked matches found for tonight's shows.").pack()
            return
        # Table rows
        for pb in self.prebookings:
            var = tk.BooleanVar(value=False)
            rowf = ttk.Frame(self.matches_frame)
            rowf.pack(fill=tk.X, pady=1)
            cb = ttk.Checkbutton(rowf, variable=var)
            cb.pack(side=tk.LEFT)
            ttk.Label(rowf, text=str(getattr(pb, 'Booking_Name', '')), width=40, anchor='w').pack(side=tk.LEFT)
            ttk.Label(rowf, text=str(getattr(pb, 'CardUID', '')), width=10).pack(side=tk.LEFT)
            # Winner selection
            winner_var = tk.StringVar()
            # Query involved workers for this match
            cursor2 = self.conn.cursor()
            cursor2.execute("SELECT Involved FROM tblPreBookingInvolvedMatch WHERE PreBookingUID = ?", (pb.UID,))
            winner_options = [str(row[0]) for row in cursor2.fetchall()]
            cursor2.close()
            winner_combo = ttk.Combobox(rowf, values=winner_options, textvariable=winner_var, width=18, state="readonly")
            winner_combo.pack(side=tk.LEFT)
            self.match_vars.append((var, pb))
            self.winner_vars.append((winner_var, pb, winner_options))

    def check_all_matches(self):
        for var, _ in self.match_vars:
            var.set(True)

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
        # 1. Only book checked matches
        selected = [(pb, winner_var.get()) for (var, pb), (winner_var, _, _) in zip(self.match_vars, self.winner_vars) if var.get()]
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
        for i, (pb, winner_uid) in enumerate(selected):
            new_uid = max_uid + i + 1
            new_order = max_order + i + 1
            referee = random.choice(referees) if referees else None
            roadagent = random.choice(roadagents) if roadagents else None
            cursor.execute("""
                INSERT INTO tblUserBooking (
                    UID, Segment_Name, MainShow, PostShow, Segment_Order, Match, MatchUID, OverallRating, Referee, RoadAgent, Belt1, Belt2, Belt3, Announcer1, Announcer2, Announcer3, Length, Major, PreBookingUID, Completed, Problematic, ABFlag, ABRating, ABMin, ABMax, AngleOutput, Scripted
                )
                SELECT ?, Booking_Name, 1, 0, ?, Match, MatchUID, -1, ?, ?, Belt1, Belt2, Belt3, ?, ?, ?, Length, Major, UID, 0, 0, 0, NULL, NULL, NULL, AngleOutput, Scripted
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
            # Add winner note if winner selected
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
