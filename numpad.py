import customtkinter as ctk

class TimeNumpad(ctk.CTkToplevel):
    def __init__(self, parent, entry):
        super().__init__(parent)
        self.entry = entry
        self.title("Numpad Time")
        self.configure(bg="white")
        
        self.update()
        

        self.geometry("400x500+350+50")
        self.update_idletasks()
        

        self.transient(parent)
        self.lift()
        self.focus_force()
        
        self.protocol("WM_DELETE_WINDOW", self.close_numpad)

        # === กรอบปุ่มตัวเลข ===
        frame = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=15)
        frame.pack(pady=20)

        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("0", 3, 1), ("⌫", 3, 2)
        ]

        for text, row, col in buttons:
            btn = ctk.CTkButton(
                frame, text=text, font=("Arial", 28, "bold"),
                width=80, height=80, corner_radius=15
            )
            btn.configure(command=lambda x=text: self.on_button_click(x))
            btn.grid(row=row, column=col, padx=8, pady=8)

        # === ปุ่ม ล้าง / OK ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        clear_btn = ctk.CTkButton(
            btn_frame, text="🗑 ล้าง", fg_color="#e63946", hover_color="#d62828",
            font=("Arial", 24, "bold"), width=120, height=60, corner_radius=15
        )
        clear_btn.configure(command=self.clear_entry)
        clear_btn.pack(side="left", padx=15)

        ok_btn = ctk.CTkButton(
            btn_frame, text="✔ OK", fg_color="#2d6a4f", hover_color="#1b4332",
            font=("Arial", 24, "bold"), width=120, height=60, corner_radius=15
        )
        ok_btn.configure(command=self.close_numpad)
        ok_btn.pack(side="left", padx=15)
    
    def on_button_click(self, value):
        current_text = self.entry.get()
    
        if value == "⌫":
            if len(current_text) > 0:

                self.entry.delete(len(current_text) - 1, "end")
        elif len(current_text) < 5:

            if len(current_text) == 2 and ":" not in current_text:
                self.entry.insert("end", ":")
            self.entry.insert("end", value)
    
    def clear_entry(self):

        self.entry.delete(0, "end")
    
    def close_numpad(self):
        text = self.entry.get()
        if len(text) == 4:
            self.entry.insert(2, ":")
        elif len(text) != 5:
            self.entry.delete(0, "end")
        self.destroy()


# === ตัวอย่างการใช้งาน ===
def open_time_numpad():
    TimeNumpad(root, entry)

root = ctk.CTk()
root.geometry("1024x600")

entry = ctk.CTkEntry(root, font=("Arial", 32), width=300, height=60)
entry.pack(pady=40)

btn_open_numpad = ctk.CTkButton(
    root, text="⏰ เปิด Numpad เวลา",
    font=("Arial", 28, "bold"),
    width=250, height=70,
    corner_radius=20,
    command=open_time_numpad
)
btn_open_numpad.pack()

root.mainloop()