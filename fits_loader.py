# fits_loader.py
# Loads and normalizes FITS files for Ecliptica animations

import os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_interp
import astroalign

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
    """
    with fits.open(path, memmap=False) as hdul:
        data = hdul[0].data

    if data is None:
        raise ValueError(f"No image data found in {path}")

    data = np.nan_to_num(data, nan=0.0)

    vmin, vmax = np.percentile(data, (stretch_min_percent, stretch_max_percent))
    scaled = np.clip((data - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)

    return Image.fromarray(scaled)

def align_to_reference(reference_path, target_path):
    """
    Attempts to align the target image to the WCS of the reference image.
    Falls back to astroalign if WCS fails. Returns a PIL 8-bit grayscale image.
    Raises an exception if all alignment methods fail.
    """
    try:
        with fits.open(reference_path, memmap=False) as ref_hdul:
            ref_data = np.nan_to_num(ref_hdul[0].data, nan=0.0)
            ref_header = ref_hdul[0].header
            ref_wcs = WCS(ref_header)

        with fits.open(target_path, memmap=False) as target_hdul:
            target_data = np.nan_to_num(target_hdul[0].data, nan=0.0)
            target_header = target_hdul[0].header
            target_wcs = WCS(target_header)

        aligned_data, _ = reproject_interp(
            (target_data, target_wcs),
            ref_wcs,
            shape_out=ref_data.shape
        )

        if not np.any(np.isfinite(aligned_data)) or np.nanmax(aligned_data) == np.nanmin(aligned_data):
            raise ValueError("Reprojection returned invalid image.")

        aligned_data = np.nan_to_num(aligned_data, nan=0.0)
        vmin, vmax = np.percentile(aligned_data, (1, 99))
        if vmax - vmin == 0:
            raise ValueError("Reprojected image has no contrast.")

        scaled = np.clip((aligned_data - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(scaled)

    except Exception as wcs_error:
        print(f"⚠️ WCS alignment failed for {target_path}: {wcs_error}")
        print(f"🔁 Attempting astroalign fallback...")

        try:
            aligned = astroalign.register(target_data, ref_data)[0]
            vmin, vmax = np.percentile(aligned, (1, 99))
            if vmax - vmin == 0:
                raise ValueError("Astroalign result has no contrast.")
            scaled = np.clip((aligned - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)
            return Image.fromarray(scaled)
        except Exception as aa_error:
            print(f"❌ Astroalign also failed for {target_path}: {aa_error}")
            raise RuntimeError(f"Failed to align {target_path} by any method.")
