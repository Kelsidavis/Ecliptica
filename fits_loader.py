# fits_loader.py
# Loads and normalizes FITS files for Ecliptica animations

import os
import numpy as np
from astropy.io import fits
from PIL import Image

def find_fits_files(folder):
    """
    Recursively finds all FITS files in a given folder.
    Returns a sorted list of full file paths.
    """
    fits_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.fits') or file.lower().endswith('.fit'):
                fits_files.append(os.path.join(root, file))
    return sorted(fits_files)

def load_fits_image(path, stretch_min_percent=1, stretch_max_percent=99):
    """
    Loads a FITS file and applies a linear stretch to scale it into an 8-bit grayscale PIL Image.
    Stretching is based on percentile clipping to improve visibility.
    """
    with fits.open(path, memmap=False) as hdul:
        data = hdul[0].data

    if data is None:
        raise ValueError(f"No image data found in {path}")

    # Flatten NaNs
    data = np.nan_to_num(data, nan=0.0)

    # Clip extreme values based on percentiles
    vmin, vmax = np.percentile(data, (stretch_min_percent, stretch_max_percent))

    # Scale to 0-255
    scaled = np.clip((data - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)

    # Convert to PIL image
    image = Image.fromarray(scaled)

    return image
