# unzipper.py
import zipfile
import tempfile
import os
import shutil

def extract_zip(zip_path):
    """
    Extracts a ZIP file into a temporary directory.
    Returns the path to the extracted folder.
    Raises a clear exception if extraction fails.
    """
    temp_dir = tempfile.mkdtemp(prefix="ecliptica_")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    except zipfile.BadZipFile:
        raise Exception(f"The file is not a valid ZIP archive: {zip_path}")
    except Exception as e:
        raise Exception(f"Failed to extract ZIP: {e}")

    return temp_dir

def cleanup_temp_dir(temp_dir):
    """
    Deletes a temporary directory created during ZIP extraction.
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
