import math
import re

import click


def format_execute_footer(n_successful, n_failed, duration, terminal_width):
    message = []
    if n_successful:
        message.append(click.style(f"{n_successful} succeeded", fg="green"))
    if n_failed:
        message.append(click.style(f"{n_failed} failed", fg="red"))
    message = " " + ", ".join(message) + " "

    color = "red" if n_failed else "green"
    message += click.style(f"in {duration} second(s) ", fg=color)

    formatted_message = _wrap_string_ignoring_ansi_colors(
        message, color, terminal_width
    )

    return formatted_message


def _wrap_string_ignoring_ansi_colors(message, color, width):
    n_characters = width - len(_remove_ansi_colors(message))
    n_left, n_right = math.floor(n_characters / 2), math.ceil(n_characters / 2)

    return (
        click.style("=" * n_left, fg=color)
        + message
        + click.style("=" * n_right, fg=color)
    )


def _remove_ansi_colors(string):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string)
