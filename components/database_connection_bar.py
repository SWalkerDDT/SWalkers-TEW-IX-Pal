import tkinter as tk
from tkinter import filedialog, messagebox
from models.database import Database
import os
import shutil

class DatabaseConnectionBar(tk.Frame):
    def __init__(self, parent, on_connect_callback=None):
        super().__init__(parent)
        self.db_path_var = tk.StringVar()
        self.db_path_var.set("C:/Users/terox/Documents/Grey Dog Software/TEW9/Databases/Default/SaveGames/Test1/temp/TEW9Save.mdb")  # Default empty
        tk.Label(self, text="Access .mdb file:").pack(side="left", padx=5)
        tk.Entry(self, textvariable=self.db_path_var, width=60).pack(side="left", padx=5)
        self.browse_btn = tk.Button(self, text="Browse", command=self.browse_mdb)
        self.browse_btn.pack(side="left", padx=5)
        self.lock_btn = tk.Button(self, text="Lock", command=self.toggle_lock)
        self.lock_btn.pack(side="left", padx=5)
        self.permanent_var = tk.BooleanVar()
        self.permanent_check = tk.Checkbutton(self, text="Connect permanently?", variable=self.permanent_var, command=self.update_button_states)
        self.permanent_check.pack(side="left", padx=5)
        self.connect_btn = tk.Button(self, text="Connect", command=self.connect_db)
        self.connect_btn.pack(side="left", padx=5)
        self.close_btn = tk.Button(self, text="Close", command=self.close_db)
        self.close_btn.pack(side="left", padx=5)
        self.on_connect_callback = on_connect_callback
        self.db = None
        self.conn_original = None
        self.conn_cached = None
        self.browse_locked = False
        self.update_button_states()

    def update_button_states(self):
        # If locked, disable Browse, Connect, and Close
        if self.browse_locked:
            self.browse_btn.config(state="disabled")
            self.connect_btn.config(state="disabled")
            self.close_btn.config(state="disabled")
            self.lock_btn.config(text="Unlock")
            return
        # If 'Connect permanently?' is not checked, disable Connect and Close
        if not self.permanent_var.get():
            self.connect_btn.config(state="disabled")
            self.close_btn.config(state="disabled")
        else:
            if self.db is not None and self.conn_original is not None and self.conn_cached is not None:
                self.connect_btn.config(state="disabled")
                self.close_btn.config(state="normal")
            else:
                self.connect_btn.config(state="normal")
                self.close_btn.config(state="disabled")
        # Browse and Lock are enabled unless connected or locked
        if self.db is not None and self.conn_original is not None and self.conn_cached is not None:
            self.browse_btn.config(state="disabled")
            self.lock_btn.config(state="disabled")
        else:
            self.browse_btn.config(state="normal")
            self.lock_btn.config(state="normal")
        self.lock_btn.config(text="Unlock" if self.browse_locked else "Lock")

    def browse_mdb(self):
        file_path = filedialog.askopenfilename(
            title="Select Access Database",
            filetypes=[("Access Database", "*.mdb")]
        )
        if file_path:
            self.db_path_var.set(file_path)

    def connect_db(self):
        if self.permanent_var.get():
            if not messagebox.askyesno("Permanent Connection", "Are you sure?"):
                return
        db_path = self.db_path_var.get()
        if db_path:
            # Connect to original
            self.db = Database(backend='access', db_path=db_path)
            self.conn_original = self.db.get_connection()
            # Prepare cached folder and copy file
            cached_dir = os.path.join(os.path.dirname(db_path), "cached")
            os.makedirs(cached_dir, exist_ok=True)
            cached_path = os.path.join(cached_dir, os.path.basename(db_path))
            shutil.copy2(db_path, cached_path)
            # Connect to cached
            self.db_cached = Database(backend='access', db_path=cached_path)
            self.conn_cached = self.db_cached.get_connection()
            if self.on_connect_callback:
                self.on_connect_callback(self.db)
            print("Connected to original:", db_path)
            print("Connected to cached:", cached_path)
        else:
            print("No file selected.")
        # After connecting, disable Browse and Lock
        self.browse_btn.config(state="disabled")
        self.lock_btn.config(state="disabled")
        self.update_button_states()

    def close_db(self):
        if self.permanent_var.get():
            if not messagebox.askyesno("Permanent Connection", "Are you sure?"):
                return
        # Close only the original connection if present
        if self.db is not None and self.conn_original is not None:
            try:
                self.db.close_connection(self.conn_original)
                print("Original database connection closed.")
            except Exception as e:
                print(f"Error closing original connection: {e}")
            self.conn_original = None
        # Do NOT close the cached connection
        # self.conn_cached remains open
        self.db = None
        # After closing, enable Browse and Lock
        self.browse_btn.config(state="normal")
        self.lock_btn.config(state="normal")
        self.update_button_states()

    def toggle_lock(self):
        if not self.browse_locked:
            # On locking, connect and close one time
            db_path = self.db_path_var.get()
            if db_path:
                temp_db = Database(backend='access', db_path=db_path)
                temp_conn = temp_db.get_connection()
                print("Connected to (Lock):", db_path)
                try:
                    temp_db.close_connection(temp_conn)
                    print("Database connection closed (Lock).")
                except Exception as e:
                    print(f"Error closing connection (Lock): {e}")
            else:
                print("No file selected for Lock.")
                self.browse_locked = not self.browse_locked
                self.update_button_states()
                print(f"Error closing connection (Lock): {e}")
        else:
            print("No file selected for Lock.")
        self.browse_locked = not self.browse_locked
        self.update_button_states()
