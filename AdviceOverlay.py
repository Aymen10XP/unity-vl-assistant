import tkinter as tk
from tkinter import font

class AdviceOverlay:
    """Legacy always-on-top window used by the original screenshot prototype."""

    def __init__(self):
        """Create and style the Tkinter window and its wrapped advice label."""

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
        """Replace visible advice and immediately process pending UI events."""

        self.label.config(text=text)
        self.root.update()
    
    def run(self):
        """Enter Tkinter's event loop until the learner closes the overlay."""

        self.root.mainloop()
