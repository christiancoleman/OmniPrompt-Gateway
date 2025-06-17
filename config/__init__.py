"""
OmniPrompt Gateway - Configuration Management

This module handles all configuration loading, environment variables,
and model setup for the application.
"""

from .environment import (
	load_environment,
	get_mcp_config,
	get_env_var,
	get_env_float,
	get_env_bool
)
from .models import get_models, validate_model_config

__all__ = [
	'load_environment',
	'get_mcp_config', 
	'get_env_var',
	'get_env_float',
	'get_env_bool',
	'get_models',
	'validate_model_config'
]
