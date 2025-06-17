"""
MCP (Model Context Protocol) integration for OmniPrompt Gateway
"""
import os
from typing import Optional, Any
from rich.console import Console

from config import get_mcp_config, get_env_var, get_env_bool

console = Console()


class MCPManager:
	"""Manages MCP client initialization and integration"""
	
	def __init__(self):
		self.mcp_client: Optional[Any] = None
		self.mcp_available = False
		self.simple_mcp_client = None
		self.integrate_mcp_simple = None
		self.extract_and_execute_tool_calls = None
		
		# Load MCP configuration
		self._load_mcp_config()
	
	def _load_mcp_config(self):
		"""Load MCP configuration and imports"""
		self.mcp_available, self.simple_mcp_client, self.integrate_mcp_simple, self.extract_and_execute_tool_calls = get_mcp_config()
	
	def initialize_mcp(self, chat_instance) -> Optional[Any]:
		"""
		Initialize MCP client if available and enabled
		
		Args:
			chat_instance: The LLMChat instance to integrate with
			
		Returns:
			MCP client instance or None if not available/enabled
		"""
		if not self.mcp_available:
			return None
			
		if not get_env_bool('ENABLE_MCP', True):
			return None
			
		if self.simple_mcp_client is None:
			return None
		
		try:
			self.mcp_client = self.simple_mcp_client()
			fs_path = get_env_var('MCP_FILESYSTEM_PATH', os.getcwd())
			# Use hasattr to safely check for method existence
			if self.mcp_client is not None and hasattr(self.mcp_client, 'add_filesystem_server'):
				self.mcp_client.add_filesystem_server(fs_path)
			
			if self.integrate_mcp_simple is not None:
				self.integrate_mcp_simple(chat_instance, self.mcp_client)
				
			console.print("[green]✓ MCP filesystem tools enabled![/green]\n")
			return self.mcp_client
			
		except Exception as e:
			console.print(f"[yellow]Warning: MCP initialization failed: {e}[/yellow]")
			console.print("[dim]Continuing without MCP support...[/dim]")
			self.mcp_client = None
			return None
	
	def extract_and_execute_tools(self, response: str) -> list:
		"""
		Extract and execute MCP tool calls from a response
		
		Args:
			response: The LLM response to check for tool calls
			
		Returns:
			List of tool execution results
		"""
		if not self.mcp_client or not self.extract_and_execute_tool_calls:
			return []
			
		try:
			return self.extract_and_execute_tool_calls(response, self.mcp_client)
		except Exception as e:
			console.print(f"[yellow]Warning: MCP tool execution failed: {e}[/yellow]")
			return []
	
	def cleanup(self):
		"""Clean up MCP resources"""
		if self.mcp_client and hasattr(self.mcp_client, 'cleanup'):
			try:
				self.mcp_client.cleanup()
			except Exception as e:
				console.print(f"[yellow]Warning: MCP cleanup failed: {e}[/yellow]")
	
	def is_available(self) -> bool:
		"""Check if MCP is available and enabled"""
		return self.mcp_available and self.mcp_client is not None


# Singleton instance for global access
mcp_manager = MCPManager()
