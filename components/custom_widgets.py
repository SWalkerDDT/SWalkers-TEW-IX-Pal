import tkinter as tk
from tkinter import ttk

class InputField(ttk.Frame):
    """
    A reusable input field with a label, entry box, and optional validation.
    Usage:
        field = InputField(parent, "Name:")
        field.pack()
        value = field.get()
    """
    def __init__(self, parent, label_text, validate_func=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.validate_func = validate_func

        self.label = ttk.Label(self, text=label_text)
        self.label.pack(side="left", padx=5)

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)

        self.error_label = ttk.Label(self, text="", foreground="red")
        self.error_label.pack(side="left", padx=5)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def validate(self):
        """Run validation function if provided."""
        if self.validate_func:
            valid, msg = self.validate_func(self.get())
            if not valid:
                self.error_label.config(text=msg)
                return False
            else:
                self.error_label.config(text="")
        return True
