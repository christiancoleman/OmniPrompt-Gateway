"""
OpenAI API adapter for OmniPrompt Gateway
"""
import os
import requests
from dataclasses import asdict
from typing import List

from models import Model, Message


def openai_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for OpenAI API (also works for OpenAI-compatible APIs)"""
	# Store model_id in a local variable to avoid any reference issues
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
		r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
		r.raise_for_status()
		return r.json()["choices"][0]["message"]["content"].strip()
	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 400:
			# Try to get error details from response
			try:
				error_data = e.response.json()
				if "error" in error_data:
					error_msg = error_data["error"].get("message", "")
					if "model" in error_msg.lower() and current_model_id in error_msg:
						raise Exception(f"Invalid model ID '{current_model_id}'. Please use a valid OpenAI model like gpt-3.5-turbo or gpt-4.")
					else:
						raise Exception(f"OpenAI API error for model '{current_model_id}': {error_msg}")
			except Exception as parse_error:
				# If we can't parse the error response, fall through to generic error
				pass
			raise Exception(f"Bad request to OpenAI API. Check your model ID '{current_model_id}' is valid.")
		elif e.response.status_code == 401:
			raise Exception(f"Invalid API key for model '{current_model_id}'. Please check your OPENAI_API_KEY in .env file.")
		elif e.response.status_code == 429:
			raise Exception(f"Rate limit exceeded for model '{current_model_id}'. Please wait and try again.")
		else:
			raise Exception(f"API request failed for model '{current_model_id}': {str(e)}")
	except requests.exceptions.RequestException as e:
		raise Exception(f"Network error for model '{current_model_id}': {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format for model '{current_model_id}': {str(e)}")
