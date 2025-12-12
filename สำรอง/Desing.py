from customtkinter import CTk, CTkComboBox
# Create a custom application class "App" that inherits from CTk (Custom Tkinter)
class App(CTk):
    def __init__(self):
        # Call the constructor of the parent class (CTk) using super()
        super().__init__()
        self.title("CTkComboBox Example")

        
        # Create a CTkComboBox
        self.combo_box = CTkComboBox(self)
        self.combo_box.pack(padx=20, pady=20)
        # Adding values
        self.combo_box.configure(values=["Option 1", "Option 2", "Option 3"])
        # Connecting it to a callback function to print the selected option on click event
        self.combo_box.configure(command=self.combobox_callback)

    def combobox_callback(self,choice):
        print("combobox dropdown clicked:", choice)

app = App()
app.mainloop()