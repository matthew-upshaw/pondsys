# pondsys.persistence.model_storage.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.'

import os
import pickle
import tkinter as tk
from tkinter import filedialog

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

def save_model(model):
    """
    Prompts the user for a filename and saves the model to a file using pickle.
    """
    logger.info("Saving model...")

    root = tk.Tk()

    file_path = filedialog.asksaveasfilename(
        title="Save Model",
        defaultextension=".pond",
        filetypes=[("PondSys Model", "*.pond"), ("All Files", "*.*")],
    )

    root.destroy()

    if not file_path:
        logger.warning("No file selected. Model not saved.")
        return
    
    try:
        with open(file_path, "wb") as f:
            pickle.dump(model, f)
        logger.info(TextStyler.GREEN+f"Model saved to {file_path}."+TextStyler.RESET)
        model.is_modified = False
    except Exception as e:
        logger.error(f"Error saving model to {file_path}: {e}")

def load_model():
    """
    Prompts the user for a filename and loads the model from a file using pickle.
    """
    logger.info("Loading model...")

    root = tk.Tk()

    file_path = filedialog.askopenfilename(
        title="Load Model",
        filetypes=[("PondSys Model", "*.pond"), ("All Files", "*.*")],
    )

    root.destroy()

    if not file_path:
        logger.warning("No file selected. Model not loaded.")
        return None
    
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} does not exist.")
        return None
    
    try:
        with open(file_path, "rb") as f:
            model = pickle.load(f)
        logger.info(TextStyler.GREEN+f"Model loaded from {file_path}."+TextStyler.RESET)
        return model
    except Exception as e:
        logger.error(f"Error loading model from {file_path}: {e}")
        return None
