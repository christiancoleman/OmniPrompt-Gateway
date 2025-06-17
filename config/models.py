"""
Model configuration management for OmniPrompt Gateway
"""
import requests
from typing import Dict, List, Tuple
import os

from models import Model
from adapters import openai_chat, claude_chat, ollama_chat
from .environment import get_env_var, get_env_float


# Provider configurations
PROVIDER_CONFIGS = {
	"openai": {
		"endpoint_env": "OPENAI_API_ENDPOINT",
		"default_endpoint": "https://api.openai.com/v1/chat/completions",
		"auth_env": "OPENAI_API_KEY",
		"auth_header": "Bearer {}",
		"adapter": openai_chat,
	},
	"anthropic": {
		"endpoint_env": "ANTHROPIC_API_ENDPOINT",
		"default_endpoint": "https://api.anthropic.com/v1/messages",
		"auth_env": "ANTHROPIC_API_KEY",
		"auth_header": "x-api-key: {}",
		"adapter": claude_chat,
	},
	"local-lmstudio": {
		"endpoint_env": "LM_STUDIO_ENDPOINT",
		"default_endpoint": "http://localhost:1234/v1/chat/completions",
		"auth_env": None,
		"auth_header": "",
		"adapter": openai_chat,  # LM Studio uses OpenAI-compatible API
	},
	"local-ollama": {
		"endpoint_env": "OLLAMA_ENDPOINT",
		"default_endpoint": "http://localhost:11434/api/chat",
		"auth_env": None,
		"auth_header": "",
		"adapter": ollama_chat,
	}
}


def get_provider_models(provider: str) -> List[str]:
	"""Get list of models for a provider from environment"""
	models_env = f"{provider.upper().replace('-', '_')}_MODELS"
	models_str = get_env_var(models_env, "")
	
	if not models_str:
		# Default models if none specified
		defaults = {
			"openai": ["gpt-3.5-turbo", "gpt-4"],
			"anthropic": ["claude-3-sonnet-20240229"],
			"local-lmstudio": ["local-model"],
			"local-ollama": ["llama2"]
		}
		return defaults.get(provider, [])
	
	# Parse comma-separated list
	return [m.strip() for m in models_str.split(",") if m.strip()]


def set_provider_models(provider: str, models: List[str]):
	"""Update provider models in environment"""
	models_env = f"{provider.upper().replace('-', '_')}_MODELS"
	os.environ[models_env] = ",".join(models)


def check_local_availability(provider: str, endpoint: str) -> bool:
	"""Check if a local provider is available"""
	if provider == "local-lmstudio":
		try:
			# Check LM Studio models endpoint
			r = requests.get(endpoint.replace("/chat/completions", "/models"), timeout=1)
			return r.status_code == 200
		except:
			return False
	elif provider == "local-ollama":
		try:
			# Check Ollama API endpoint
			r = requests.get(endpoint.replace("/api/chat", "/api/tags"), timeout=1)
			return r.status_code == 200
		except:
			return False
	return True


def get_models() -> Dict[str, Model]:
	"""Load model configurations from environment"""
	models = {}
	
	# Get the generic system prompt (used as fallback for all models)
	generic_prompt = get_env_var("GENERIC_SYSTEM_PROMPT", "You are a helpful assistant.")
	
	for provider, config in PROVIDER_CONFIGS.items():
		# Skip providers without API keys (except local ones)
		if config["auth_env"] and not get_env_var(config["auth_env"]):
			continue
		
		# Get provider-specific settings
		provider_key = provider.upper().replace("-", "_")
		endpoint = get_env_var(config["endpoint_env"], config["default_endpoint"])
		system_prompt = get_env_var(f"{provider_key}_SYSTEM_PROMPT", generic_prompt)
		temperature = get_env_float(f"{provider_key}_TEMPERATURE", 0.7)
		max_tokens = int(get_env_var(f"{provider_key}_MAX_TOKENS", "4096"))
		
		# Skip local providers if not available
		if provider.startswith("local-") and not check_local_availability(provider, endpoint):
			continue
		
		# Get models for this provider
		model_list = get_provider_models(provider)
		
		for model_id in model_list:
			# Use model_id as the key (e.g., "gpt-4", "claude-3-opus-20240229")
			models[model_id] = Model(
				name=model_id,  # Use model_id as name for clarity
				provider=provider,
				endpoint=endpoint,
				model_id=model_id,
				auth_env=config["auth_env"],
				auth_header=config["auth_header"],
				system_prompt=system_prompt,
				adapter=config["adapter"],
				temperature=temperature,
				max_tokens=max_tokens
			)
	
	return models


def get_available_providers() -> List[Tuple[str, bool, List[str]]]:
	"""
	Get list of all providers with their availability status and current models
	
	Returns:
		List of tuples: (provider_name, is_available, model_list)
	"""
	providers = []
	
	for provider, config in PROVIDER_CONFIGS.items():
		# Check if provider is available
		available = False
		
		if config["auth_env"]:
			# API-based provider
			available = bool(get_env_var(config["auth_env"]))
		else:
			# Local provider
			endpoint = get_env_var(config["endpoint_env"], config["default_endpoint"])
			available = check_local_availability(provider, endpoint)
		
		# Get current models
		model_list = get_provider_models(provider) if available else []
		
		providers.append((provider, available, model_list))
	
	return providers


def validate_model_config(models: Dict[str, Model]) -> tuple[list[str], list[str]]:
	"""
	Validate model configurations and return missing keys and warnings
	
	Args:
		models: Dictionary of configured models
		
	Returns:
		tuple: (missing_keys, warnings)
	"""
	missing_keys = []
	warnings = []
	
	# Check each provider
	for provider, config in PROVIDER_CONFIGS.items():
		if config["auth_env"] and not get_env_var(config["auth_env"]):
			missing_keys.append(f"{provider} ({config['auth_env']})")
	
	# Add specific warnings for common issues
	if not models:
		warnings.append("No models configured. Please set up at least one API key.")
	
	return missing_keys, warnings
