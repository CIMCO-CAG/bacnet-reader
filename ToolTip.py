import tkinter as tk
from tkinter import ttk

class CreateToolTip(object):
    """
    Create a modern tooltip for a given widget
    """
    def __init__(self, widget, text='Widget Info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.tooltip = None

    def enter(self, event=None):
        self.show_tooltip()

    def leave(self, event=None):
        self.hide_tooltip()

    def show_tooltip(self):
        if not self.tooltip:
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 10
            y += self.widget.winfo_rooty() + 25

            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")

            frame = ttk.Frame(self.tooltip, style="Tooltip.TFrame")
            frame.pack(padx=5, pady=5)

            label = ttk.Label(frame, text=self.text, style="Tooltip.TLabel")
            label.pack()

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
