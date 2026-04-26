"""Context types for message handling"""

from enum import Enum


class ContextType(Enum):
    """Message context types"""
    TEXT = 1
    IMAGE = 2
    VOICE = 3
    FILE = 4
    VIDEO = 5
