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
	headers = {
		"Content-Type": "application/json"
	}
	if model.auth_env:
		api_key = os.getenv(model.auth_env)
		if api_key:
			headers["Authorization"] = model.auth_header.format(api_key)
	
	payload = {
		"model": model.model_id,
		"messages": [asdict(msg) for msg in messages],
		"temperature": model.temperature,
		"max_tokens": model.max_tokens
	}
	
	try:
		r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
		r.raise_for_status()
		return r.json()["choices"][0]["message"]["content"].strip()
	except requests.exceptions.RequestException as e:
		raise Exception(f"API request failed: {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format: {str(e)}")
