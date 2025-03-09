# pondsys.cli.menus.file_management_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.persistence.model_storage import save_model, load_model

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def file_management_menu(beam):
    """
    Submenu for file management.
    """

    while True:
        file_choice = questionary.select(
            "File Management Menu",
            choices=[
                "Create Model",
                "Save Model",
                "Load Model",
                "Back to Main Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Back to main menu
        if file_choice == "Back to Main Menu":
            break

        # Creating a beam class
        elif file_choice == "Create Model":
            name = questionary.text(
                "Description:"
            ).ask()
            length = questionary.text(
                "Length of beam (ft):"
            ).ask()
            try:
                beam = Beam(float(length), name)
                logger.info(TextStyler.GREEN+f"Created {name} with beam of length {length} ft."+TextStyler.RESET)
                return beam
            except Exception as e:
                logger.error(f"Error creating beam: {e}")

        # Saving the model
        elif file_choice == "Save Model":
            if beam is None:
                logger.warning("No beam created. Please create a beam first.")
            else:
                save_model(beam)
                return beam

        # Loading a model
        elif file_choice == "Load Model":
            loaded_beam = load_model()
            if loaded_beam is not None:
                beam = loaded_beam
                return beam
            else:
                logger.warning("Failed to load beam.")
