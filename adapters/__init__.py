"""
OmniPrompt Gateway - API Adapters

This module contains all the API adapters for different LLM providers.
"""

from .base import AdapterProtocol, BaseAdapter
from .openai import openai_chat
from .claude import claude_chat
from .ollama import ollama_chat

__all__ = [
	'AdapterProtocol', 
	'BaseAdapter',
	'openai_chat', 
	'claude_chat', 
	'ollama_chat'
]
