import tkinter as tk
import tkinter.ttk as ttk
from components.base_tab_frame import BaseTabFrame

class PreBookingPage(BaseTabFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        