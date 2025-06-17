"""
Message data model for OmniPrompt Gateway
"""
from dataclasses import dataclass


@dataclass
class Message:
	"""Represents a single message in a conversation"""
	role: str
	content: str
