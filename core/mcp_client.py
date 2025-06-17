"""
Robust MCP Client - Handles MCP server communication and startup issues
"""
import json
import subprocess
import sys
import os
import time
import threading
import tempfile
from typing import Dict, List, Optional, Any

from rich.console import Console

console = Console()


class RobustMCPClient:
	"""MCP client that handles npx issues gracefully"""
	
	def __init__(self):
		self.servers = {}
		self.available_tools = {}
		
	def add_filesystem_server(self, allowed_path: str = "."):
		"""Add a filesystem MCP server with robust startup"""
		# Convert to absolute path
		allowed_path = os.path.abspath(allowed_path)
		
		# Try different methods to start the server
		methods = [
			# Method 1: Direct npx with explicit package
			{
				'name': 'npx with package.json',
				'command': self._get_npx_command_with_package(allowed_path)
			},
			# Method 2: Pre-installed global package
			{
				'name': 'global install',
				'command': self._get_global_command(allowed_path)
			},
			# Method 3: Standard npx
			{
				'name': 'standard npx',
				'command': ["npx", "-y", "@modelcontextprotocol/server-filesystem", allowed_path]
			}
		]
		
		for method in methods:
			console.print(f"[dim]Trying {method['name']}...[/dim]")
			try:
				if method['command']:
					self._add_server("fs", method['command'])
					console.print(f"[green]✓ Success with {method['name']}[/green]")
					return
			except Exception as e:
				console.print(f"[yellow]✗ {method['name']} failed: {str(e)[:50]}...[/yellow]")
				continue
				
		raise RuntimeError(
			"Could not start MCP filesystem server. Try:\n"
			"1. npm install -g @modelcontextprotocol/server-filesystem\n"
			"2. Restart your terminal\n"
			"3. Run this script again"
		)
	
	def _get_npx_command_with_package(self, allowed_path: str) -> Optional[List[str]]:
		"""Try to use npx with a pre-created package.json"""
		try:
			# Create a temporary directory with package.json
			temp_dir = tempfile.mkdtemp()
			
			package_json = {
				"name": "mcp-temp",
				"version": "1.0.0",
				"dependencies": {
					"@modelcontextprotocol/server-filesystem": "latest"
				}
			}
			
			package_path = os.path.join(temp_dir, "package.json")
			with open(package_path, 'w') as f:
				json.dump(package_json, f)
			
			# Install dependencies
			result = subprocess.run(
				["npm", "install"],
				cwd=temp_dir,
				capture_output=True,
				text=True,
				shell=True
			)
			
			if result.returncode == 0:
				# Use the installed package
				server_path = os.path.join(
					temp_dir, 
					"node_modules", 
					"@modelcontextprotocol", 
					"server-filesystem", 
					"dist", 
					"index.js"
				)
				if os.path.exists(server_path):
					return ["node", server_path, allowed_path]
					
		except:
			pass
		return None
	
	def _get_global_command(self, allowed_path: str) -> Optional[List[str]]:
		"""Try to find globally installed MCP server"""
		# Common locations for global npm packages
		possible_commands = [
			["mcp-server-filesystem", allowed_path],
			["server-filesystem", allowed_path],
		]
		
		for cmd in possible_commands:
			try:
				# Test if command exists
				result = subprocess.run(
					[cmd[0], "--help"],
					capture_output=True,
					shell=True
				)
				if result.returncode == 0:
					return cmd
			except:
				pass
				
		# Try to find the global npm installation
		try:
			result = subprocess.run(
				["npm", "root", "-g"],
				capture_output=True,
				text=True,
				shell=True
			)
			if result.returncode == 0:
				global_path = result.stdout.strip()
				server_path = os.path.join(
					global_path,
					"@modelcontextprotocol",
					"server-filesystem",
					"dist",
					"index.js"
				)
				if os.path.exists(server_path):
					return ["node", server_path, allowed_path]
		except:
			pass
			
		return None
		
	def _add_server(self, name: str, command: List[str]):
		"""Start an MCP server as a subprocess"""
		console.print(f"[dim]Starting server with command: {' '.join(command[:3])}...[/dim]")
		
		# Prepare the command
		use_shell = sys.platform == "win32"
		if use_shell:
			cmd_str = " ".join(f'"{c}"' if ' ' in c else c for c in command)
		else:
			cmd_str = command
			
		# Start the process
		process = subprocess.Popen(
			cmd_str,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			bufsize=0,  # Unbuffered
			shell=use_shell,
			env={**os.environ, 'NODE_NO_WARNINGS': '1'}  # Suppress Node warnings
		)
		
		self.servers[name] = {
			'process': process,
			'request_id': 0,
			'command': command
		}
		
		# Wait a bit for server to start
		time.sleep(0.5)
		
		# Check if process is still running
		if process.poll() is not None:
			stderr = process.stderr.read() if process.stderr is not None else ""
			raise RuntimeError(f"Server exited immediately. Error: {stderr}")
		
		# Initialize the server
		console.print("[dim]Initializing server...[/dim]")
		response = self._send_request(name, "initialize", {
			"protocolVersion": "2024-11-05",
			"capabilities": {}
		})
		
		if not response:
			stderr = process.stderr.read() if process.stderr is not None else ""
			raise RuntimeError(f"Failed to initialize server. No response. Stderr: {stderr}")
		
		# Get available tools
		console.print("[dim]Getting available tools...[/dim]")
		tools_response = self._send_request(name, "tools/list", {})
		if tools_response and 'result' in tools_response:
			tools = tools_response['result'].get('tools', [])
			for tool in tools:
				tool_id = f"{name}:{tool['name']}"
				self.available_tools[tool_id] = {
					'server': name,
					'name': tool['name'],
					'description': tool.get('description', ''),
					'inputSchema': tool.get('inputSchema', {})
				}
			console.print(f"[green]✓ Found {len(tools)} tools[/green]")
		
		console.print(f"[green]✓ Server '{name}' connected successfully[/green]")
		
	def _send_request(self, server_name: str, method: str, params: Dict) -> Optional[Dict]:
		"""Send a request and get response with better error handling"""
		if server_name not in self.servers:
			raise ValueError(f"Server '{server_name}' not connected")
			
		server = self.servers[server_name]
		process = server['process']
		
		# Check if process is still running
		if process.poll() is not None:
			raise RuntimeError(f"Server process has terminated")
			
		server['request_id'] += 1
		
		request = {
			"jsonrpc": "2.0",
			"method": method,
			"params": params,
			"id": server['request_id']
		}
		
		try:
			# Send request
			request_str = json.dumps(request) + '\n'
			process.stdin.write(request_str)
			process.stdin.flush()
			
			# Read response with timeout
			start_time = time.time()
			timeout = 5.0
			
			while time.time() - start_time < timeout:
				# Check if process is still alive
				if process.poll() is not None:
					stderr = process.stderr.read() if process.stderr is not None else ""
					raise RuntimeError(f"Server process died. Stderr: {stderr}")
				
				# Try to read a line
				try:
					# For Windows, we need a different approach
					if sys.platform == "win32":
						# Just try to read with a small delay
						response_line = None
						
						def read_line():
							nonlocal response_line
							response_line = process.stdout.readline()
						
						thread = threading.Thread(target=read_line)
						thread.daemon = True
						thread.start()
						thread.join(timeout=0.5)
						
						if response_line:
							return json.loads(response_line)
					else:
						# Unix-like systems
						import select
						if select.select([process.stdout], [], [], 0.1)[0]:
							line = process.stdout.readline()
							if line:
								return json.loads(line)
				except:
					pass
					
				time.sleep(0.1)
			
			# Timeout - check stderr
			stderr = process.stderr.read() if process.stderr is not None else ""
			console.print(f"[yellow]Timeout waiting for response. Stderr: {stderr}[/yellow]")
			return None
			
		except Exception as e:
			console.print(f"[yellow]Error in _send_request: {e}[/yellow]")
			return None
			
	def call_tool(self, tool_id: str, arguments: Dict[str, Any]) -> str:
		"""Call a tool and return the result"""
		if ':' in tool_id:
			server_name, tool_name = tool_id.split(':', 1)
		else:
			raise ValueError(f"Tool ID must be in format 'server:tool'")
				
		response = self._send_request(server_name, "tools/call", {
			"name": tool_name,
			"arguments": arguments
		})
		
		if response and 'result' in response:
			result = response['result']
			if isinstance(result, dict) and 'content' in result:
				return result['content']
			return str(result)
		elif response and 'error' in response:
			return f"Error: {response['error'].get('message', 'Unknown error')}"
		else:
			return "No response from tool"
			
	def get_tools_prompt(self) -> str:
		"""Get formatted tools for LLM prompt"""
		if not self.available_tools:
			return ""
			
		lines = ["\n### Available MCP Tools ###\n"]
		for tool_id, tool_info in self.available_tools.items():
			lines.append(f"Tool: {tool_id}")
			lines.append(f"Description: {tool_info['description']}")
			lines.append(f"Parameters: {json.dumps(tool_info['inputSchema'], indent=2)}")
			lines.append("")
			
		lines.append("To use a tool, respond with:")
		lines.append("```mcp-tool")
		lines.append('{"tool": "fs:read_file", "arguments": {"path": "/path/to/file.txt"}}')
		lines.append("```")
		
		return "\n".join(lines)
		
	def cleanup(self):
		"""Clean up all server processes"""
		for server_info in self.servers.values():
			process = server_info['process']
			if process.poll() is None:
				process.terminate()
				try:
					process.wait(timeout=2)
				except:
					process.kill()


def integrate_mcp_simple(chat_instance, mcp_client):
	"""Add MCP tools to an existing chat instance's system prompts"""
	tools_prompt = mcp_client.get_tools_prompt()
	
	if tools_prompt:
		for model in chat_instance.models.values():
			if tools_prompt not in model.system_prompt:
				model.system_prompt += tools_prompt
				
		if chat_instance.current_conversation:
			current = chat_instance.get_current_system_prompt()
			if current and tools_prompt not in current:
				chat_instance.update_system_prompt(current + tools_prompt)


def extract_and_execute_tool_calls(response: str, mcp_client) -> List[str]:
	"""Extract MCP tool calls from response and execute them"""
	import re
	
	results = []
	pattern = r'```mcp-tool\s*\n(.*?)\n```'
	matches = re.findall(pattern, response, re.DOTALL)
	
	for match in matches:
		try:
			tool_call = json.loads(match)
			tool_id = tool_call.get('tool')
			arguments = tool_call.get('arguments', {})
			
			if tool_id:
				result = mcp_client.call_tool(tool_id, arguments)
				results.append(f"[MCP Tool '{tool_id}' Result]:\n{result}")
		except Exception as e:
			results.append(f"[MCP Error]: {str(e)}")
			
	return results
