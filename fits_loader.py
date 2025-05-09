# fits_loader.py
import os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_interp
import astroalign
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor


def find_fits_files(folder):
    fits_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.fits') or file.lower().endswith('.fit'):
                fits_files.append(os.path.join(root, file))
    return sorted(fits_files)


def load_fits_image(path, vmin=None, vmax=None):
    with fits.open(path, memmap=False) as hdul:
        data = hdul[0].data

    if data is None:
        raise ValueError(f"No image data found in {path}")

    data = np.nan_to_num(data, nan=0.0)

    if vmin is None or vmax is None:
        vmin, vmax = np.percentile(data, (1, 99))

    scaled = np.clip((data - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(scaled)


def align_to_reference(reference_path, target_path, vmin=None, vmax=None, return_raw=False):
    """
    Aligns a FITS image to a reference WCS. Optionally returns raw float array (for global stretch scan).
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

        if return_raw:
            return aligned_data, _

        aligned_data = np.nan_to_num(aligned_data, nan=0.0)

        if vmin is None or vmax is None:
            vmin, vmax = np.percentile(aligned_data, (1, 99))

        scaled = np.clip((aligned_data - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(scaled)

    except Exception as wcs_error:
        print(f"⚠️ WCS alignment failed for {target_path}: {wcs_error}")
        print(f"🔁 Attempting astroalign fallback...")

        try:
            aligned = astroalign.register(target_data, ref_data)[0]

            if return_raw:
                return aligned, None

            vmin = np.percentile(aligned, 1) if vmin is None else vmin
            vmax = np.percentile(aligned, 99) if vmax is None else vmax

            scaled = np.clip((aligned - vmin) / (vmax - vmin) * 255.0, 0, 255).astype(np.uint8)
            return Image.fromarray(scaled)
        except Exception as aa_error:
            print(f"❌ Astroalign also failed for {target_path}: {aa_error}")
            raise RuntimeError(f"Failed to align {target_path} by any method.")


def load_fits_data_for_stretch(path, reference_path=None, use_alignment=True):
    """
    Loads FITS data for global stretching. Can align if needed.
    """
    try:
        if reference_path and use_alignment:
            data, _ = align_to_reference(reference_path, path, return_raw=True)
        else:
            with fits.open(path, memmap=False) as hdul:
                data = hdul[0].data

        if data is not None:
            return np.nan_to_num(data, nan=0.0).flatten()
    except Exception as e:
        print(f"⚠️ Failed to load FITS for stretch: {path} - {e}")
    
    return None


def get_global_stretch_limits(fits_paths, reference_path=None):
    """
    Multithreaded version: loads all FITS frames in parallel and computes global vmin/vmax.
    """
    all_data = []

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = []
        for path in fits_paths:
            futures.append(executor.submit(load_fits_data_for_stretch, path, reference_path))

        for future in futures:
            data = future.result()
            if data is not None:
                all_data.append(data)

    if not all_data:
        raise ValueError("No valid FITS data for global stretching.")

    stacked = np.concatenate(all_data)
    vmin = np.percentile(stacked, 1)
    vmax = np.percentile(stacked, 99)
    return vmin, vmax, stacked


def show_stretch_histogram(stacked_data, vmin, vmax):
    """
    Displays a histogram of the stacked image pixel values and marks the stretch limits.
    """
    plt.figure(figsize=(8, 4))
    plt.hist(stacked_data, bins=512, color='gray', alpha=0.7, log=True)
    plt.axvline(vmin, color='red', linestyle='--', label=f'vmin = {vmin:.2f}')
    plt.axvline(vmax, color='blue', linestyle='--', label=f'vmax = {vmax:.2f}')
    plt.title("Global Pixel Value Histogram")
    plt.xlabel("Pixel Value")
    plt.ylabel("Log Count")
    plt.legend()
    plt.tight_layout()
    plt.show()
