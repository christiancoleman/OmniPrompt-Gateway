"""
OmniPrompt Gateway - Core Logic

This module contains the core chat functionality and MCP integration.
"""

from .chat import LLMChat
from .mcp_integration import MCPManager, mcp_manager

__all__ = [
	'LLMChat',
	'MCPManager', 
	'mcp_manager'
]
