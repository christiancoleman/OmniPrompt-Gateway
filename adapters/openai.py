"""
OpenAI API adapter for OmniPrompt Gateway
"""
import os
import requests
from dataclasses import asdict
from typing import List, Dict, Optional

from models import Model, Message


class OpenAIAdapter:
	"""Adapter supporting both Chat Completions and Responses API"""
	
	def __init__(self):
		# Cache for Responses API conversation states
		self.response_cache: Dict[str, str] = {}  # model_name -> last_response_id
	
	def __call__(self, model: Model, messages: List[Message]) -> str:
		"""Route to appropriate API based on model configuration"""
		if model.api_type == "responses":
			return self.responses_api(model, messages)
		else:
			return self.chat_completions_api(model, messages)
	
	def chat_completions_api(self, model: Model, messages: List[Message]) -> str:
		"""Standard Chat Completions API implementation"""
		current_model_id = model.model_id
		
		headers = {
			"Content-Type": "application/json"
		}
		if model.auth_env:
			api_key = os.getenv(model.auth_env)
			if api_key:
				headers["Authorization"] = model.auth_header.format(api_key)
		
		payload = {
			"model": current_model_id,
			"messages": [asdict(msg) for msg in messages],
			"temperature": model.temperature,
			"max_tokens": model.max_tokens
		}
		
		try:
			delim("Chat Completions API payload")
			debug(payload)
			r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
			r.raise_for_status()
			delim("Chat Completions API response")
			debug(r.json())
			return r.json()["choices"][0]["message"]["content"].strip()
		except Exception as e:
			return self._handle_error(e, current_model_id)
	
	def responses_api(self, model: Model, messages: List[Message]) -> str:
		"""Responses API implementation with stateful conversations"""
		current_model_id = model.model_id
		cache_key = model.name  # Use model name as cache key
		
		headers = {
			"Content-Type": "application/json"
		}
		if model.auth_env:
			api_key = os.getenv(model.auth_env)
			if api_key:
				headers["Authorization"] = model.auth_header.format(api_key)
		
		# Get the last user message
		user_messages = [m for m in messages if m.role == "user"]
		if not user_messages:
			raise Exception("No user message found")
		
		last_user_message = user_messages[-1].content
		
		# Check if this is a continuation
		previous_response_id = self.response_cache.get(cache_key)
		
		payload = {
			"model": current_model_id,
			"input": last_user_message
			#"temperature": model.temperature,
			#"max_output_tokens": model.max_tokens
		}
		
		# Add previous response ID if continuing conversation
		if previous_response_id:
			payload["previous_response_id"] = previous_response_id
		else:
			# First message - include system prompt if available
			system_messages = [m for m in messages if m.role == "system"]
			if system_messages:
				payload["instructions"] = system_messages[0].content
		
		try:
			delim("Responses API payload")
			debug(payload)
			r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
			r.raise_for_status()
			delim("Responses API response")
			debug(r.json())
			response_data = r.json()
			
			# Cache the response ID for next call
			self.response_cache[cache_key] = response_data["id"]
			
			# Extract the response text
			if "output_text" in response_data:
				print(0)
				return response_data["output_text"].strip()
			elif "output" in response_data and response_data["output"]:
				# Handle structured output format
				output_messages = response_data["output"]
				print(1)
				if output_messages and isinstance(output_messages, list):
					print(2)
					first_msg = output_messages[0]
					second_msg = output_messages[1] if len(output_messages) > 1 else None
					print(first_msg)
					print(second_msg)
					if "content" in first_msg and isinstance(first_msg["content"], list):
						print(3)
						for content in first_msg["content"]:
							print(4)
							if content.get("type") == "output_text":
								print(5)
								return content.get("text", "").strip()
					print(6)
					if second_msg and "content" in second_msg and isinstance(second_msg["content"], list):
						for content in second_msg["content"]:
							print(7)
							if content.get("type") == "output_text":
								print(85)
								return content.get("text", "").strip()
			
			raise Exception(f"Unexpected Responses API format for model '{current_model_id}'")
			
		except Exception as e:
			return self._handle_error(e, current_model_id)
	
	def clear_cache(self, model_name: Optional[str] = None):
		"""Clear cached response IDs"""
		if model_name:
			self.response_cache.pop(model_name, None)
		else:
			self.response_cache.clear()
	
	def _handle_error(self, error: Exception, model_id: str) -> str:
		"""Common error handling for both APIs"""
		if isinstance(error, requests.exceptions.HTTPError):
			if error.response.status_code == 400:
				try:
					error_data = error.response.json()
					if "error" in error_data:
						error_msg = error_data["error"].get("message", "")
						if "model" in error_msg.lower() and model_id in error_msg:
							raise Exception(f"Invalid model ID '{model_id}'. Please use a valid OpenAI model like gpt-3.5-turbo or gpt-4.")
						else:
							raise Exception(f"OpenAI API error for model '{model_id}': {error_msg}")
				except:
					pass
				raise Exception(f"Bad request to OpenAI API. Check your model ID '{model_id}' is valid.")
			elif error.response.status_code == 401:
				raise Exception(f"Invalid API key for model '{model_id}'. Please check your OPENAI_API_KEY in .env file.")
			elif error.response.status_code == 429:
				raise Exception(f"Rate limit exceeded for model '{model_id}'. Please wait and try again.")
			else:
				raise Exception(f"API request failed for model '{model_id}': {str(error)}")
		elif isinstance(error, requests.exceptions.RequestException):
			raise Exception(f"Network error for model '{model_id}': {str(error)}")
		else:
			raise error


# Create a singleton instance
openai_adapter_instance = OpenAIAdapter()

# Export the main function for backward compatibility
def openai_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for OpenAI API (also works for OpenAI-compatible APIs)"""
	return openai_adapter_instance(model, messages)

def delim(thing: str):
	print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
	print("%%%%%%%%%%%%%%%%%%%%%%" + thing + "%%%%%%%%%%%%%%%%%%%%%%")

from typing import Any

def debug(toDump: Any):
	"""Debug function to print JSON payloads"""
	try:
		import json as json_module
		print(json_module.dumps(toDump, indent=4))
	except Exception as e:
		print(f"Error printing JSON: {str(e)}")