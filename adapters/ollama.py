"""
Ollama API adapter for OmniPrompt Gateway
"""
import requests
from dataclasses import asdict
from typing import List

from models import Model, Message


def ollama_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for Ollama local models"""
	payload = {
		"model": model.model_id,
		"messages": [asdict(msg) for msg in messages],
		"options": {
			"temperature": model.temperature,
			"num_predict": model.max_tokens
		},
		"stream": False
	}
	
	try:
		r = requests.post(model.endpoint, json=payload, timeout=120)
		r.raise_for_status()
		return r.json()["message"]["content"].strip()
	except requests.exceptions.RequestException as e:
		raise Exception(f"API request failed: {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format: {str(e)}")
