# Ecliptica

**Ecliptica** creates time-lapse animations from calibrated FITS images — optimized for ZIPs exported by [Astrocalibrator](https://github.com/Kelsidavis/astrocalibrator) — using fast, multithreaded processing.

---

## Features

- 📦 Drag and drop ZIP archives of calibrated FITS frames
- ⚡ Multithreaded loading, alignment, and animation generation
- 🔭 Global brightness normalization for smooth, flicker-free animations
- 🎞️ Output high-quality GIF or MP4 time-lapse videos
- 🖥️ Responsive, simple user interface with live progress
- 📈 Automatic histogram display of pixel distribution
- 🔒 Automatic file cleanup after processing

---

## How It Works

1. Use **[Astrocalibrator](https://github.com/Kelsidavis/astrocalibrator)** to generate calibrated FITS images with flat, dark, and bias frame correction.
2. Drop the resulting ZIP file onto Ecliptica.
3. Ecliptica extracts, aligns, and globally stretches all frames for consistent brightness.
4. Choose your output format (GIF or MP4).
5. The animation is saved alongside the original ZIP using a matching filename.

---

## Requirements

- Python 3.8+
- Recommended packages:

```bash
pip install numpy astropy reproject astroalign Pillow matplotlib opencv-python tkinterdnd2
```

Or install from `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Example

![Example Animation](https://your-link-to-demo-gif.gif)

*(Replace with a real example if you have one!)*

---

## Roadmap

- [ ] Batch processing of multiple ZIPs
- [ ] Parallelized GIF/MP4 encoding
- [ ] Asteroid/track detection overlay
- [ ] Save histogram PNG with animation
- [ ] Cancel button and logging panel

---

## License

MIT License

---

## Credits

Created with ❤️ for astrophotographers by Kelsi Davis.

Originally designed to pair with [Astrocalibrator](https://github.com/Kelsidavis/astrocalibrator).
