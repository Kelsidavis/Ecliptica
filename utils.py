# utils.py
# Utility functions for Ecliptica: timestamp extraction, file sorting, and helpers

from astropy.io import fits
import os
from datetime import datetime

def get_timestamp_from_fits(path):
    """
    Extracts and returns a timestamp from the FITS header.
    Falls back to file modified time if header value is missing.
    Returns a datetime object.
    """
    try:
        with fits.open(path, memmap=False) as hdul:
            header = hdul[0].header
            date_obs = header.get('DATE-OBS')
            if date_obs:
                return datetime.fromisoformat(date_obs.replace('Z', ''))
    except Exception:
        pass

    # Fallback to file modified time
    return datetime.fromtimestamp(os.path.getmtime(path))

def sort_files_by_timestamp(file_paths):
    """
    Sorts a list of FITS file paths based on DATE-OBS or file modified time.
    Returns a new sorted list.
    """
    return sorted(file_paths, key=get_timestamp_from_fits)
