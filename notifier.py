# notifier.py
import tkinter as tk
import customtkinter as ctk

class Notifier:
    def __init__(self, parent):
        self.parent = parent
        self.active_notification = None

    def show_notification(self, message, success=True, duration=2500):
        if self.active_notification:
            try:
                self.active_notification.destroy()
            except:
                pass

        color = "#4CAF50" if success else "#F44336"
        frame = ctk.CTkFrame(self.parent, fg_color=color, corner_radius=0)
        label = ctk.CTkLabel(frame, text=message, text_color="white", font=("TH Sarabun New", 20, "bold"))
        label.pack(padx=20, pady=10)

        frame.place(relx=0.99, rely=0.02, anchor="ne")
        self.active_notification = frame
        self.parent.after(duration, frame.destroy)
