"""
Base adapter interface for OmniPrompt Gateway
"""
from abc import ABC, abstractmethod
from typing import List, Protocol, Any

from models import Model, Message


class AdapterProtocol(Protocol):
	"""Protocol defining the interface for LLM adapters"""
	
	def __call__(self, model: Model, messages: List[Message]) -> str:
		"""
		Send messages to an LLM and return the response
		
		Args:
			model: Model configuration containing endpoint, auth, etc.
			messages: List of messages in the conversation
			
		Returns:
			The model's response as a string
			
		Raises:
			Exception: If the API request fails or response is invalid
		"""
		...


class BaseAdapter(ABC):
	"""Base class for LLM adapters (optional, can use protocol instead)"""
	
	@abstractmethod
	def __call__(self, model: Model, messages: List[Message]) -> str:
		"""Send messages to an LLM and return the response"""
		pass
		
	def _handle_request_error(self, error: Any) -> Exception:
		"""Convert various request errors into a standard format"""
		# Check if it's a requests exception with response attribute
		if hasattr(error, 'response') and error.response is not None:
			if hasattr(error.response, 'status_code'):
				return Exception(f"API request failed with status {error.response.status_code}: {str(error)}")
		return Exception(f"API request failed: {str(error)}")
		
	def _handle_response_error(self, error: Exception) -> Exception:
		"""Convert response parsing errors into a standard format"""
		return Exception(f"Unexpected response format: {str(error)}")
