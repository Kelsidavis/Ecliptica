from tkinterdnd2 import TkinterDnD
import tkinter as tk

root = TkinterDnD.Tk()
root.title("Simple TkinterDnD2 Test")
root.geometry("400x200")

label = tk.Label(root, text="Drag files here", bg="black", fg="white")
label.pack(expand=True, fill="both")

root.mainloop()
