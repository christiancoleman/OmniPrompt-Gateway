"""
OmniPrompt Gateway - CLI Interface

This module contains all the command-line interface functionality.
"""

from .interface import CLIInterface
from .commands import CommandHandler
from .formatting import (
	print_formatted_response,
	print_help,
	print_models_table,
	print_grouped_models,
	print_conversation_history,
	print_error,
	print_warning,
	print_success,
	print_info,
	print_mcp_tool_result,
	create_status_display
)

__all__ = [
	'CLIInterface',
	'CommandHandler',
	'print_formatted_response',
	'print_help',
	'print_models_table',
	'print_grouped_models',
	'print_conversation_history',
	'print_error',
	'print_warning',
	'print_success',
	'print_info',
	'print_mcp_tool_result',
	'create_status_display'
]
