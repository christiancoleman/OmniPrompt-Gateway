"""
Conversation data model for OmniPrompt Gateway
"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

from .message import Message


@dataclass
class Conversation:
	"""Represents a conversation with a specific model"""
	model_name: str
	messages: List[Message] = field(default_factory=list)
	created_at: datetime = field(default_factory=datetime.now)
