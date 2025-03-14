# pondsys.cli.menus.beam_def_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def beam_def_menu(beam):
    """
    Submenu for managing beam definition (i.e. length, size, slope, etc.)
    """
    while True:
        action = questionary.select(
            "Beam Definition Menu:",
            choices=[
                "Assign Beam Length",
                "Assign Beam Section",
                "Assign Beam Slope",
                "Assign Tributary Width",
                "Back to Main Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to main menu
        if action == "Back to Main Menu":
            break

        # Assign beam length
        elif action == "Assign Beam Length":
            length = questionary.text(
                f"Enter new beam length (ft) - Currently {beam.length}:"
            ).ask()
            try:
                beam.length = float(length)
                logger.info(TextStyler.GREEN+f"Assigned beam length of {length} ft."+TextStyler.RESET)
            except Exception as e:
                logger.error(f"Error assigning beam length: {e}")

        # Assign beam section
        elif action == "Assign Beam Section":
            section = questionary.text(
                f"Update beam section (e.g. W12x26, 14K1, 16KCS2) - Currently {beam.section}:"
            ).ask()
            try:
                beam.add_or_update_section(section.upper())
                logger.info(TextStyler.GREEN+f"Assigned size {section.upper()} to beam."+TextStyler.RESET)
            except Exception as e:
                logger.error(f"Error assigning beam section: {e}")

        # Assign beam slope
        elif action == "Assign Beam Slope":
            slope = questionary.text(
                f"Enter beam slope (in/ft) - Currently {beam.beam_slope}:"
            ).ask()
            try:
                beam.add_or_update_beam_slope(float(slope))
                logger.info(TextStyler.GREEN+f"Assigned slope of {slope} in/ft to beam."+TextStyler.RESET)
            except Exception as e:
                logger.error(f"Error assigning beam slope: {e}")

        elif action == "Assign Tributary Width":
            width = questionary.text(
                f"Enter tributary width (ft) - Currently {beam.tributary_width}:"
            ).ask()
            try:
                beam.add_or_update_tributary_width(float(width))
                logger.info(TextStyler.GREEN+f"Assigned tributary width of {width} ft."+TextStyler.RESET)
            except Exception as e:
                logger.error(f"Error assigning tributary width: {e}")