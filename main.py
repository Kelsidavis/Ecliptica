# main.py
# Main GUI and control flow for Ecliptica

from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import tempfile
import pathlib

import unzipper
import fits_loader
import animator
import utils


class EclipticaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ecliptica - FITS Time-Lapse Animator")
        self.root.geometry("500x450")
        self.root.configure(bg='black')

        # User settings
        self.output_format = tk.StringVar(value="GIF")
        self.frame_duration = tk.IntVar(value=100)  # ms for GIF, used to derive FPS for MP4
        self.include_timestamps = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0)

        self.setup_ui()

    def setup_ui(self):
        self.label = tk.Label(
            self.root,
            text="Drag and drop a ZIP file of calibrated FITS images",
            bg='black',
            fg='white',
            font=("Arial", 12)
        )
        self.label.pack(pady=20)

        # Drag-and-drop setup
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

        # Manual file browse
        self.button = tk.Button(
            self.root,
            text="Or click to browse",
            command=self.browse_zip,
            bg='gray20',
            fg='white'
        )
        self.button.pack(pady=10)

        # Output format selection
        format_frame = tk.Frame(self.root, bg='black')
        format_frame.pack(pady=10)
        tk.Label(format_frame, text="Output Format:", bg='black', fg='white').pack(side='left')
        tk.Radiobutton(format_frame, text="GIF", variable=self.output_format, value="GIF", bg='black', fg='white').pack(side='left')
        tk.Radiobutton(format_frame, text="MP4", variable=self.output_format, value="MP4", bg='black', fg='white').pack(side='left')

        # Frame speed selector
        speed_frame = tk.Frame(self.root, bg='black')
        speed_frame.pack(pady=10)
        tk.Label(speed_frame, text="Frame Duration (ms):", bg='black', fg='white').pack(side='left')
        self.speed_scale = tk.Scale(speed_frame, from_=10, to=500, orient='horizontal', variable=self.frame_duration, bg='black', fg='white')
        self.speed_scale.pack(side='left')

        # Timestamp overlay toggle
        self.timestamp_check = tk.Checkbutton(
            self.root,
            text="Include timestamps",
            variable=self.include_timestamps,
            bg='black',
            fg='white',
            selectcolor='black',
            activebackground='black'
        )
        self.timestamp_check.pack(pady=10)

        # Progress bar
        self.progress = tk.Scale(
            self.root,
            from_=0, to=100,
            orient='horizontal',
            variable=self.progress_var,
            showvalue=False,
            length=400,
            state='disabled',
            bg='black',
            troughcolor='gray20',
            highlightthickness=0
        )
        self.progress.pack(pady=10)

    def browse_zip(self):
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if path:
            self.process_zip(path)

    def handle_drop(self, event):
        raw_path = event.data.strip('{}').strip('"')
        path = pathlib.Path(raw_path).resolve()
        path = str(path)

        print(f"Received drop path: {path}")

        if os.path.isfile(path) and path.lower().endswith('.zip'):
            self.process_zip(path)
        else:
            messagebox.showerror("Invalid File", f"Invalid ZIP file:\n{path}")

    def process_zip(self, zip_path):
        try:
            temp_dir = unzipper.extract_zip(zip_path)
            fits_files = fits_loader.find_fits_files(temp_dir)

            if not fits_files:
                raise Exception("No FITS files found in ZIP.")

            fits_files = utils.sort_files_by_timestamp(fits_files)

            frames = []
            for i, fits_path in enumerate(fits_files):
                frame = fits_loader.load_fits_image(fits_path)

                if self.include_timestamps.get():
                    timestamp = utils.get_timestamp_from_fits(fits_path)
                    text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    frame = animator.draw_timestamp_on_image(frame, text)

                frames.append(frame)

                # Update progress
                percent = (i + 1) / len(fits_files) * 100
                self.progress_var.set(percent)
                self.root.update_idletasks()

            # Suggest filename based on ZIP
            base_name = os.path.splitext(os.path.basename(zip_path))[0]
            suggested_filename = base_name + (".gif" if self.output_format.get() == "GIF" else ".mp4")

            save_path = filedialog.asksaveasfilename(
                defaultextension=".gif" if self.output_format.get() == "GIF" else ".mp4",
                filetypes=[("GIF files", "*.gif"), ("MP4 files", "*.mp4")],
                title="Save Animation As",
                initialfile=suggested_filename
            )

            if save_path:
                if self.output_format.get() == "GIF":
                    animator.save_gif(frames, save_path, duration=self.frame_duration.get())
                else:
                    fps = max(1, 1000 // self.frame_duration.get())
                    animator.save_mp4(frames, save_path, fps=fps)

                messagebox.showinfo("Success", f"Animation saved to:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")
        finally:
            if 'temp_dir' in locals():
                unzipper.cleanup_temp_dir(temp_dir)
            self.progress_var.set(0)

if __name__ == "__main__":
    print("Launching Ecliptica...")
    root = TkinterDnD.Tk()
    app = EclipticaApp(root)
    root.mainloop()
