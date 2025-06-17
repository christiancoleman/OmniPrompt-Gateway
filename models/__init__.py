"""
OmniPrompt Gateway - Data Models

This module contains all the core data structures used throughout the application.
"""

from .message import Message
from .model import Model
from .conversation import Conversation

__all__ = ['Message', 'Model', 'Conversation']
