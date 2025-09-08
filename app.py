import tkinter as tk
from tkinter import filedialog, ttk
from models.database import Database

from views.page_home import HomePage
from views.page_settings import SettingsPage
from views.page_tableview import TableViewPage
from views.page_alliance import AllianceManagerPage
from views.page_dojo import DojoManagerPage
from views.page_roundrobin import RoundRobinPage
from views.page_prebooking import PreBookingPage

from components.database_connection_bar import DatabaseConnectionBar

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SWalkers TEW IX Pal")
        self.geometry("1200x800")

        self.db_bar = DatabaseConnectionBar(self, on_connect_callback=self.on_db_connected)
        self.db_bar.pack(side="top", fill="x")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.frames = {}
        for F in (HomePage, SettingsPage, TableViewPage, AllianceManagerPage, DojoManagerPage, RoundRobinPage, PreBookingPage):
            page_name = F.__name__
            frame = F(parent=self.notebook, controller=self)
            self.frames[page_name] = frame
            self.notebook.add(frame, text=page_name.replace('Page', ''))

        self.db_connection = None

    def show_frame(self, page_name):
        # Not needed with tabs, but kept for compatibility
        frame = self.frames[page_name]
        frame.tkraise()

    def on_db_connected(self, db):
        # Store the db connection and propagate to all frames
        self.db_connection = db
        for frame in self.frames.values():
            if hasattr(frame, 'set_db_connection'):
                frame.set_db_connection(db)
