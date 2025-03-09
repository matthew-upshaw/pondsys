# pondsys.cli.menus.file_management_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.persistence.model_storage import save_model, load_model

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
                print(f"Created {name} with beam of length {length} ft.")
                return beam
            except Exception as e:
                print('Error creating beam:', e)

        # Saving the model
        elif file_choice == "Save Model":
            if beam is None:
                print("No beam created. Please create a beam first.")
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
                print("Failed to load beam.")
