"""
Claude API adapter for OmniPrompt Gateway
"""
import os
import requests
from typing import List

from models import Model, Message


def claude_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for Claude API (Anthropic)"""
	headers = {
		"Content-Type": "application/json",
		"anthropic-version": "2023-06-01"
	}
	if model.auth_env:
		api_key = os.getenv(model.auth_env)
		if api_key:
			headers["x-api-key"] = api_key
	
	# Convert messages to Claude format
	claude_messages = []
	for msg in messages:
		if msg.role != "system":  # Claude handles system prompts differently
			claude_messages.append({
				"role": msg.role,
				"content": msg.content
			})
	
	# Extract system prompt if present
	system_prompt = next((msg.content for msg in messages if msg.role == "system"), model.system_prompt)
	
	payload = {
		"model": model.model_id,
		"messages": claude_messages,
		"max_tokens": model.max_tokens,
		"temperature": model.temperature,
		"system": system_prompt
	}
	
	try:
		r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
		r.raise_for_status()
		return r.json()["content"][0]["text"].strip()
	except requests.exceptions.RequestException as e:
		raise Exception(f"API request failed: {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format: {str(e)}")
