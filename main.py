# main.py
# Main GUI and control flow for Ecliptica

from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import tempfile
import pathlib
import threading

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

        self.output_format = tk.StringVar(value="GIF")
        self.frame_duration = tk.IntVar(value=100)
        self.include_timestamps = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0)
        self._pulse_timer = None

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

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

        self.button = tk.Button(
            self.root,
            text="Or click to browse",
            command=self.browse_zip,
            bg='gray20',
            fg='white'
        )
        self.button.pack(pady=10)

        format_frame = tk.Frame(self.root, bg='black')
        format_frame.pack(pady=10)
        tk.Label(format_frame, text="Output Format:", bg='black', fg='white').pack(side='left')
        tk.Radiobutton(format_frame, text="GIF", variable=self.output_format, value="GIF", bg='black', fg='white').pack(side='left')
        tk.Radiobutton(format_frame, text="MP4", variable=self.output_format, value="MP4", bg='black', fg='white').pack(side='left')

        speed_frame = tk.Frame(self.root, bg='black')
        speed_frame.pack(pady=10)
        tk.Label(speed_frame, text="Frame Duration (ms):", bg='black', fg='white').pack(side='left')
        self.speed_scale = tk.Scale(speed_frame, from_=10, to=500, orient='horizontal', variable=self.frame_duration, bg='black', fg='white')
        self.speed_scale.pack(side='left')

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
            self.start_processing_thread(path)

    def handle_drop(self, event):
        raw_path = event.data.strip('{}').strip('"')
        path = pathlib.Path(raw_path).resolve()
        path = str(path)

        print(f"Received drop path: {path}")
        if os.path.isfile(path) and path.lower().endswith('.zip'):
            self.start_processing_thread(path)
        else:
            messagebox.showerror("Invalid File", f"Invalid ZIP file:\n{path}")

    def start_processing_thread(self, zip_path):
        self.root.after(0, self.lock_input)
        thread = threading.Thread(target=self.process_zip_safe, args=(zip_path,))
        thread.daemon = True
        thread.start()

    def process_zip_safe(self, zip_path):
        try:
            self.process_zip(zip_path)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{e}"))
        finally:
            self.root.after(0, self.stop_pulsing)
            self.root.after(0, lambda: self.progress_var.set(0))
            self.root.after(0, self.unlock_input)

    def process_zip(self, zip_path):
        temp_dir = unzipper.extract_zip(zip_path)
        fits_files = fits_loader.find_fits_files(temp_dir)

        if not fits_files:
            raise Exception("No FITS files found in ZIP.")

        fits_files = utils.sort_files_by_timestamp(fits_files)
        reference_fits = fits_files[0]

        vmin, vmax, stacked_data = fits_loader.get_global_stretch_limits(fits_files, reference_fits)
        self.root.after(0, lambda: fits_loader.show_stretch_histogram(stacked_data, vmin, vmax))


        frames = []
        for i, fits_path in enumerate(fits_files):
            self.root.after(0, self.start_pulsing)
            try:
                if i == 0:
                    frame = fits_loader.load_fits_image(fits_path, vmin=vmin, vmax=vmax)
                else:
                    frame = fits_loader.align_to_reference(reference_fits, fits_path, vmin=vmin, vmax=vmax)
            finally:
                self.root.after(0, self.stop_pulsing)

            if self.include_timestamps.get():
                timestamp = utils.get_timestamp_from_fits(fits_path)
                text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                frame = animator.draw_timestamp_on_image(frame, text)

            frames.append(frame)

            percent = (i + 1) / len(fits_files) * 100
            self.root.after(0, lambda p=percent: self.progress_var.set(p))

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

            self.root.after(0, lambda: messagebox.showinfo("Success", f"Animation saved to:\n{save_path}"))

        unzipper.cleanup_temp_dir(temp_dir)

    def pulse_progress(self):
        current = self.progress_var.get()
        next_val = current + 1 if current < 99 else 0
        self.progress_var.set(next_val)
        self._pulse_timer = self.root.after(50, self.pulse_progress)

    def start_pulsing(self):
        self._pulse_timer = self.root.after(0, self.pulse_progress)

    def stop_pulsing(self):
        if self._pulse_timer:
            self.root.after_cancel(self._pulse_timer)
            self._pulse_timer = None

    def lock_input(self):
        self.button.config(state="disabled")
        self.root.dnd_unbind('<<Drop>>')
        self.root.title("Ecliptica - Working...")

    def lock_input(self):
        self.button.config(state="disabled")
        self.root.dnd_bind('<<Drop>>', lambda e: None)
        self.root.title("Ecliptica - Working...")



if __name__ == "__main__":
    print("Launching Ecliptica...")
    root = TkinterDnD.Tk()
    app = EclipticaApp(root)
    root.mainloop()
