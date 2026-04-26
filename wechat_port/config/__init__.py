"""Configuration module"""

import os


# Default configuration
_config = {
    "agent_workspace": os.path.expanduser("~/cow"),
}


def conf():
    """Get configuration dictionary"""
    return _config


def load_config(config_dict: dict):
    """Load configuration from dictionary

    Args:
        config_dict: Configuration dictionary to merge with default config
    """
    _config.update(config_dict)
