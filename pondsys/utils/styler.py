# pondsys.utils.styler.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

class TextStyler:
    """
    A class to store ANSI color codes for terminal output.
    """

    # Reset
    RESET = "\033[0m"

    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BLACK_BG = "\033[40m"
    RED_BG = "\033[41m"
    GREEN_BG = "\033[42m"
    YELLOW_BG = "\033[43m"
    BLUE_BG = "\033[44m"
    MAGENTA_BG = "\033[45m"
    CYAN_BG = "\033[46m"
    WHITE_BG = "\033[47m"

    # Bold text
    BOLD = "\033[1m"

    # Underline text
    UNDERLINE = "\033[4m"

    # Inverted text
    INVERTED = "\033[7m"

    # Strikethrough text
    STRIKETHROUGH = "\033[9m"

    # Invisible text
    INVISIBLE = "\033[8m"

    # Reset all
    RESET_ALL = "\033[0m\033[39m\033[49m"

    # Reset text
    RESET_TEXT = "\033[39m"

    # Reset background
    RESET_BG = "\033[49m"

    # Reset bold
    RESET_BOLD = "\033[22m"

    # Reset underline
    RESET_UNDERLINE = "\033[24m"

    # Reset inverted
    RESET_INVERTED = "\033[27m"

    # Reset strikethrough
    RESET_STRIKETHROUGH = "\033[29m"

    # Reset invisible
    RESET_INVISIBLE = "\033[28m"

    # Reset all but text
    RESET_ALL_BUT_TEXT = "\033[0m\033[49m"

    # Reset all but background
    RESET_ALL_BUT_BG = "\033[0m\033[39m"

    # Reset all but bold
    RESET_ALL_BUT_BOLD = "\033[0m\033[22m"

    # Reset all but underline
    RESET_ALL_BUT_UNDERLINE = "\033[0m\033[24m"

    def style_text(self, text, *style):
        """
        Apply one or more styles to a text.

        Parameters:
            text (str): The text to style.
            style (str): The style to apply.

        Returns:
            str: The styled text.
        """
        style_prefix = "".join(style)
        return f"{style_prefix}{text}"