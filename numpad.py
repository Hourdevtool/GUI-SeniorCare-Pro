import customtkinter as ctk

class TimeNumpad(ctk.CTkToplevel):
    def __init__(self, parent, entry):
        super().__init__(parent)
        self.title("Numpad Time")
        self.geometry("300x400")
        self.entry = entry
        self.configure(bg="white")
        self.attributes("-topmost", True)  # ทำให้หน้าต่างอยู่ด้านหน้าตลอด
        self.protocol("WM_DELETE_WINDOW", self.close_numpad)  # ปิดแล้วคืนค่า

        frame = ctk.CTkFrame(self)
        frame.pack(pady=10)

        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("0", 3, 1), ("⌫", 3, 2)
        ]

        for text, row, col in buttons:
            ctk.CTkButton(frame, text=text, font=("Arial", 20), width=60, height=60, 
                          command=lambda x=text: self.on_button_click(x)).grid(row=row, column=col, padx=5, pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="🗑 ล้าง", fg_color="red", font=("Arial", 18), width=80, 
                      command=self.clear_entry).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="✔ OK", fg_color="green", font=("Arial", 18), width=80, 
                      command=self.close_numpad).pack(side="left", padx=10)

    def on_button_click(self, value):
        current_text = self.entry.get()

        if value == "⌫":
            self.entry.delete(len(current_text) - 1, "end")
        elif len(current_text) < 5:  # จำกัดความยาวที่ 5 ตัวอักษร (HH:MM)
            if len(current_text) == 2 and ":" not in current_text:
                self.entry.insert("end", ":")  # ใส่ `:` อัตโนมัติ
            self.entry.insert("end", value)

    def clear_entry(self):
        self.entry.delete(0, "end")  # ล้างข้อมูลในช่องป้อนค่า

    def close_numpad(self):
        text = self.entry.get()
        if len(text) == 4:  # ถ้าผู้ใช้ใส่แค่ HHMM ให้ใส่ ":" อัตโนมัติ
            self.entry.insert(2, ":")
        elif len(text) != 5:  # ถ้าใส่ไม่ครบ ให้เคลียร์
            self.entry.delete(0, "end")
        self.destroy()

def open_time_numpad():
    TimeNumpad(root, entry)

root = ctk.CTk()
root.geometry("400x200")

entry = ctk.CTkEntry(root, font=("Arial", 24), width=250)
entry.pack(pady=20)

btn_open_numpad = ctk.CTkButton(root, text="⏰ เปิด Numpad เวลา", font=("Arial", 20), width=200, command=open_time_numpad)
btn_open_numpad.pack()

root.mainloop()
