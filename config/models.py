"""
Model configuration management for OmniPrompt Gateway
"""
import requests
from typing import Dict

from models import Model
from adapters import openai_chat, claude_chat, ollama_chat
from .environment import get_env_var, get_env_float


def get_models() -> Dict[str, Model]:
	"""Load model configurations from environment or use defaults"""
	models = {}
	
	# Get the generic system prompt (used as fallback for all models)
	generic_prompt = get_env_var("GENERIC_SYSTEM_PROMPT", "You are a helpful assistant.")
	
	# OpenAI GPT-4
	if get_env_var("OPENAI_API_KEY"):
		models["gpt4"] = Model(
			name="gpt4",
			endpoint=get_env_var("OPENAI_API_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
			model_id=get_env_var("OPENAI_MODEL", "gpt-4"),
			auth_env="OPENAI_API_KEY",
			auth_header="Bearer {}",
			system_prompt=get_env_var("GPT4_SYSTEM_PROMPT", generic_prompt),
			adapter=openai_chat,
			temperature=get_env_float("GPT4_TEMPERATURE", 0.7)
		)
		
		# GPT-3.5
		models["gpt3.5"] = Model(
			name="gpt3.5",
			endpoint=get_env_var("OPENAI_API_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
			model_id="gpt-3.5-turbo",
			auth_env="OPENAI_API_KEY",
			auth_header="Bearer {}",
			system_prompt=get_env_var("GPT35_SYSTEM_PROMPT", generic_prompt),
			adapter=openai_chat,
			temperature=get_env_float("GPT35_TEMPERATURE", 0.7)
		)
	
	# Claude
	if get_env_var("ANTHROPIC_API_KEY"):
		models["claude"] = Model(
			name="claude",
			endpoint=get_env_var("CLAUDE_API_ENDPOINT", "https://api.anthropic.com/v1/messages"),
			model_id=get_env_var("CLAUDE_MODEL", "claude-3-sonnet-20240229"),
			auth_env="ANTHROPIC_API_KEY",
			auth_header="x-api-key: {}",
			system_prompt=get_env_var("CLAUDE_SYSTEM_PROMPT", generic_prompt),
			adapter=claude_chat,
			temperature=get_env_float("CLAUDE_TEMPERATURE", 0.7)
		)
	
	# LM Studio (OpenAI-compatible local server)
	lm_studio_endpoint = get_env_var("LM_STUDIO_ENDPOINT", "http://localhost:1234/v1/chat/completions")
	# Check if LM Studio is running by trying to connect
	try:
		r = requests.get(lm_studio_endpoint.replace("/chat/completions", "/models"), timeout=1)
		if r.status_code == 200:
			models["lmstudio"] = Model(
				name="lmstudio",
				endpoint=lm_studio_endpoint,
				model_id=get_env_var("LM_STUDIO_MODEL", "local-model"),
				auth_env=None,
				auth_header="",
				system_prompt=get_env_var("LM_STUDIO_SYSTEM_PROMPT", generic_prompt),
				adapter=openai_chat,  # LM Studio uses OpenAI-compatible API
				temperature=get_env_float("LM_STUDIO_TEMPERATURE", 0.7)
			)
	except:
		pass  # LM Studio not running
	
	# Ollama (local)
	ollama_endpoint = get_env_var("OLLAMA_ENDPOINT", "http://localhost:11434/api/chat")
	ollama_model = get_env_var("OLLAMA_MODEL", "llama2")
	models["ollama"] = Model(
		name="ollama",
		endpoint=ollama_endpoint,
		model_id=ollama_model,
		auth_env=None,
		auth_header="",
		system_prompt=get_env_var("OLLAMA_SYSTEM_PROMPT", generic_prompt),
		adapter=ollama_chat,
		temperature=get_env_float("OLLAMA_TEMPERATURE", 0.7)
	)
	
	return models


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
	
	# Check for missing API keys
	for name, model in models.items():
		if model.auth_env and not get_env_var(model.auth_env):
			missing_keys.append(f"{name} ({model.auth_env})")
	
	# Add specific warnings for common issues
	if not models:
		warnings.append("No models configured. Please set up at least one API key.")
	
	return missing_keys, warnings
