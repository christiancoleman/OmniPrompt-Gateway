"""
OmniPrompt Gateway - Core Logic

This module contains the core chat functionality and MCP integration.
"""

from .chat import LLMChat
from .mcp_integration import MCPManager, mcp_manager
from .mcp_client import RobustMCPClient, integrate_mcp_simple, extract_and_execute_tool_calls

__all__ = [
	'LLMChat',
	'MCPManager', 
	'mcp_manager',
	'RobustMCPClient',
	'integrate_mcp_simple',
	'extract_and_execute_tool_calls'
]
