import tkinter as tk
from tkinter import font

class AdviceOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Unity Assistant")
        self.root.attributes("-topmost", True)
        self.root.geometry("350x200+50+100")  # Position near left side
        self.root.configure(bg="#1e1e1e")
        
        self.label = tk.Label(
            self.root, text="Waiting for Unity activity...",
            wraplength=330, justify="left",
            fg="#ffffff", bg="#1e1e1e",
            font=("Segoe UI", 10)
        )
        self.label.pack(padx=10, pady=10, fill="both", expand=True)
    
    def update(self, text):
        self.label.config(text=text)
        self.root.update()
    
    def run(self):
        self.root.mainloop()