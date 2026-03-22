"""TAD - small shared utility helpers."""

from constants import FORMAT_FLOAT


def format_float(value):
    """Format a float value using the project's standard precision."""
    return format(value, FORMAT_FLOAT)
