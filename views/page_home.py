
import tkinter as tk
from components.custom_widgets import InputField
from components.base_tab_frame import BaseTabFrame

def not_empty(value):
    """Example validation: field must not be empty"""
    if not value.strip():
        return False, "Required"
    return True, ""



class HomePage(BaseTabFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tk.Label(self, text="Home Page", font=("Arial", 16)).pack(pady=20)

        self.name_field = InputField(self, "Name:", validate_func=not_empty)
        self.name_field.pack(pady=10, fill="x", padx=20)

        tk.Button(
            self, text="Save User",
            command=self.save
        ).pack(pady=5)

        tk.Button(
            self, text="Go to Settings",
            command=lambda: self.go_to_tab("Settings")
        ).pack(pady=5)

    def save(self):
        if self.name_field.validate():
            self.name_field.set("")
