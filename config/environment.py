"""
Environment configuration management for OmniPrompt Gateway
"""
import os
import sys
from typing import Any, Optional


def load_environment() -> bool:
	"""
	Load environment variables from .env file
	
	Returns:
		bool: True if .env file was loaded, False otherwise
	"""
	try:
		from dotenv import load_dotenv
		
		# Try loading .env from current directory first, then from exe directory
		env_loaded = False
		if os.path.exists('.env'):
			# Use .env in current working directory
			load_dotenv()
			env_loaded = True
			# Uncomment for debugging: print(f"Loaded .env from current directory: {os.getcwd()}")
		else:
			# Look for .env next to the executable
			if getattr(sys, 'frozen', False):
				# Running as compiled executable
				app_dir = os.path.dirname(sys.executable)
			else:
				# Running as script
				app_dir = os.path.dirname(os.path.abspath(__file__))
			
			env_path = os.path.join(app_dir, '.env')
			if os.path.exists(env_path):
				load_dotenv(env_path)
				env_loaded = True
				# Uncomment for debugging: print(f"Loaded .env from: {app_dir}")
			
		if not env_loaded:
			print(f"Note: No .env file found")
			print(f"Searched in: current directory and {app_dir if 'app_dir' in locals() else 'application directory'}")
			print(f"Create .env from .env.example and add your API keys")
			
		return env_loaded
		
	except ImportError:
		print("Error: python-dotenv not installed. Please run: pip install python-dotenv")
		sys.exit(1)


def get_mcp_config() -> tuple[bool, Optional[Any], Optional[Any], Optional[Any]]:
	"""
	Load MCP configuration and imports
	
	Returns:
		tuple: (MCP_AVAILABLE, SimpleMCPClient, integrate_mcp_simple, extract_and_execute_tool_calls)
	"""
	try:
		from core.mcp_client import RobustMCPClient as SimpleMCPClient, integrate_mcp_simple, extract_and_execute_tool_calls
		return True, SimpleMCPClient, integrate_mcp_simple, extract_and_execute_tool_calls
	except ImportError:
		print("Warning: MCP module not found. MCP features will be disabled.")
		return False, None, None, None


def get_env_var(key: str, default: str = "") -> str:
	"""Get environment variable with default value"""
	return os.getenv(key, default)


def get_env_float(key: str, default: float) -> float:
	"""Get environment variable as float with default value"""
	try:
		return float(os.getenv(key, str(default)))
	except (ValueError, TypeError):
		return default


def get_env_bool(key: str, default: bool = False) -> bool:
	"""Get environment variable as boolean with default value"""
	value = os.getenv(key, "").lower()
	if value in ("true", "1", "yes", "on"):
		return True
	elif value in ("false", "0", "no", "off"):
		return False
	return default
