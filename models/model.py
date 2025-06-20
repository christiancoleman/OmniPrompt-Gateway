"""
Model data model for OmniPrompt Gateway
"""
from dataclasses import dataclass
from typing import Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
	# Import Message for type hints
	from .message import Message


@dataclass
class Model:
	"""Configuration for a language model endpoint"""
	name: str                 # Friendly display name (now same as model_id)
	provider: str             # Provider name (openai, anthropic, local-lmstudio, local-ollama)
	endpoint: str             # Full URL of API endpoint
	model_id: str             # Model identifier
	auth_env: str | None      # Env-var that holds API key
	auth_header: str          # Header format (e.g., "Bearer {}", "x-api-key: {}")
	system_prompt: str        # Default system prompt
	adapter: Callable        # Function that does POST + parses JSON
	max_tokens: int = 4096    # Max tokens in response
	temperature: float = 0.7  # Default temperature
	
	# API type support
	api_type: str = "chat_completions"  # "chat_completions" or "responses"
	supports_api_switching: bool = False  # Whether this model can switch APIs
	api_variant_name: str | None = None   # Name of the variant when switching APIs
