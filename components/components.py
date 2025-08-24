import tkinter as tk
from tkinter import ttk

class LabeledEntry(ttk.Frame):
    """Reusable labeled entry widget"""
    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label_text)
        self.entry = ttk.Entry(self, **kwargs)

        self.label.pack(side=tk.LEFT, padx=(0, 5))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def get(self):
        return self.entry.get()

    def set(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)