"""Utility functions"""

import os


def expand_path(path: str) -> str:
    """Expand path with ~ and environment variables

    Args:
        path: Path to expand

    Returns:
        Expanded absolute path
    """
    return os.path.expanduser(os.path.expandvars(path))
