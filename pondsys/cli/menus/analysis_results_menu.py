# pondsys.cli.menus.analysis_results_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def analysis_results_menu(beam, combinations):
    """
    Submenu for viewing analysis results.
    """
    while True:
        action = questionary.select(
            "Analysis Results Menu:",
            choices=[
                "Reaction Envelope",
                "Plot Moment Envelope",
                "Plot Shear Envelope",
                "Plot Converged Ponded Depth",
                "Back to Main Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to main menu
        if action == "Back to Main Menu":
            break

        # Show the reaction envelope
        elif action == "Reaction Envelope":
            print(
                TextStyler.BOLD+
                "Reaction Envelope\n"+
                "==========================================="+
                TextStyler.RESET
            )
            for node, location in beam.support_nodes.items():
                current_envelope = beam.reaction_envelope_at_node(node, combinations)
                print(f"Node {node} at {location} ft:")
                for load_case, value in current_envelope.items():
                    print(f"  {load_case}: {value:.2f} kip")
                print("-------------------------------------------")

            questionary.press_any_key_to_continue().ask()

        # Plotting the moment envelope
        elif action == "Plot Moment Envelope":
            try:
                beam.plot_moment_envelope(combinations)
                questionary.press_any_key_to_continue().ask()
            except Exception as e:
                logger.error('Error plotting moment envelope:', e)

        # Plotting the shear envelope
        elif action == "Plot Shear Envelope":
            try:
                beam.plot_shear_envelope(combinations)
                questionary.press_any_key_to_continue().ask()
            except Exception as e:
                logger.error(f"Error plotting shear envelope: {e}")

        # Plotting the converged ponded depth
        elif action == "Plot Converged Ponded Depth":
            ponding_type = questionary.select(
                "Show Converged Depth for Ponding Due to:",
                choices=[
                    "Rain",
                    "Snow",
                ],
                use_shortcuts=True,
            ).ask()
            try:
                beam.plot_ponded_depth_history(
                    beam.analysis_stats['iterations'],
                    ponding_type.lower()
                )
                questionary.press_any_key_to_continue().ask()
            except Exception as e:
                logger.error(f"Error plotting converged ponded depth: {e}")

