# pondsys.cli.interface.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.cli.menus.file_management_menu import file_management_menu
from pondsys.cli.menus.supports_menu import supports_menu
from pondsys.cli.menus.beam_def_menu import beam_def_menu
from pondsys.cli.menus.loading_menu import loading_menu
from pondsys.cli.menus.analysis_results_menu import analysis_results_menu
from pondsys.persistence.model_storage import save_model

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def main_menu():
    """
    The main interactive CLI menu.
    """
    beam = None
    print(TextStyler.BOLD+TextStyler.CYAN+'PondSys v0.1.0-beta'+TextStyler.RESET)
    print(TextStyler.BOLD+TextStyler.CYAN+'A Ponding Analysis Tool'+TextStyler.RESET)

    while True:
        main_choice = questionary.select(
            "Main Menu",
            choices=[
                "File",
                "Beam Definition",
                "Supports",
                "Loading",
                "Perform Analysis",
                "Analysis Results",
                "Exit",
            ],
            use_shortcuts=True,
        ).ask()

        # Exiting the program
        if main_choice == "Exit":
            if beam is not None and beam.is_modified:
                save_choice = questionary.confirm(
                    "You have unsaved changes. Do you want to save before exiting?"
                ).ask()

                if bool(save_choice):
                    save_model(beam)
                    logger.info("Exiting PondSys...")
                    break                    
                else:
                    logger.info("Exiting PondSys without saving changes...")
                    break
            else:
                logger.info("Exiting PondSys...")
                break

        # Creating a beam class
        elif main_choice == "File":
            beam = file_management_menu(beam)

        # Submenu for beam definition
        elif main_choice == "Beam Definition":
            if beam is None:
                logger.warning("No beam created. Please create a beam first.")
            else:
                beam_def_menu(beam)
        
        # Submenu for managing supports
        elif main_choice == "Supports":
            if beam is None:
                logger.warning("No beam created. Please create a beam first.")
            else:
                supports_menu(beam)

        # Submenu for managing loading on the beam
        elif main_choice == "Loading":
            if beam is None:
                logger.warning("No beam created. Please create a beam first.")
            else:
                loading_menu(beam)
        
        # Submenu for managing analysis of the beam and analysis results
        elif main_choice == "Perform Analysis":
            if beam is None:
                logger.warning("No beam created. Please create a beam first.")
            else:
                try:
                    beam.analyze_ponding()
                    logger.info(TextStyler.GREEN+f"Analysis complete. Convergence reached after {beam.analysis_stats['iterations']} iterations."+TextStyler.RESET)
                except Exception as e:
                    logger.error(f"Error analyzing model:, {e}")

        elif main_choice == "Analysis Results":
            if beam is None:
                logger.warning("No beam created. Please create a beam first.")
            else:
                if beam.valid_results:
                    combinations = questionary.select(
                        "Select Load Combinations to View Results",
                        choices=[
                            'ASD',
                            'LRFD',
                        ],
                        use_shortcuts=True,
                    ).ask()
                    analysis_results_menu(beam, combinations.lower())
                else:
                    logger.warning("No valid analysis results to display.")

if __name__ == "__main__":
    main_menu()