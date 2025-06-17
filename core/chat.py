"""
Core chat functionality for OmniPrompt Gateway
"""
from typing import List, Optional
import os

from models import Message, Model, Conversation
from config import get_models


class LLMChat:
	"""Core chat functionality for managing conversations with LLMs"""
	
	def __init__(self):
		self.models = get_models()
		self.current_conversation: Optional[Conversation] = None
		self.conversations: List[Conversation] = []
		# Store custom default prompt (starts with env value or default)
		self.default_system_prompt = os.getenv("GENERIC_SYSTEM_PROMPT", "You are a helpful assistant.")
		
	def start_new_conversation(self, model_name: str, custom_prompt: Optional[str] = None):
		"""Start a new conversation with the specified model"""
		if model_name not in self.models:
			raise ValueError(f"Unknown model: {model_name}")
			
		model = self.models[model_name]
		self.current_conversation = Conversation(model_name=model_name)
		
		# Use custom prompt if provided, otherwise use model's default
		prompt = custom_prompt if custom_prompt else model.system_prompt
		
		# Add system prompt as first message
		self.current_conversation.messages.append(
			Message(role="system", content=prompt)
		)
		self.conversations.append(self.current_conversation)
		
	def add_message(self, role: str, content: str):
		"""Add a message to the current conversation"""
		if not self.current_conversation:
			raise ValueError("No active conversation")
			
		self.current_conversation.messages.append(Message(role=role, content=content))
		
	def get_response(self, user_input: str) -> str:
		"""Get response from the current model"""
		if not self.current_conversation:
			raise ValueError("No active conversation")
			
		# Add user message
		self.add_message("user", user_input)
		
		# Get model and adapter
		model = self.models[self.current_conversation.model_name]
		
		# Get response
		try:
			response = model.adapter(model, self.current_conversation.messages)
			# Add assistant response to conversation
			self.add_message("assistant", response)
			return response
		except Exception as e:
			# Remove the user message if there was an error
			self.current_conversation.messages.pop()
			raise
			
	def list_models(self) -> List[str]:
		"""List available models"""
		return list(self.models.keys())
		
	def get_conversation_history(self) -> str:
		"""Get formatted conversation history"""
		if not self.current_conversation:
			return "No active conversation"
			
		history = []
		for msg in self.current_conversation.messages:
			if msg.role != "system":  # Skip system prompts in display
				history.append(f"{msg.role.upper()}: {msg.content}")
				
		return "\n\n".join(history)
	
	def update_system_prompt(self, new_prompt: str):
		"""Update the system prompt for the current conversation"""
		if not self.current_conversation:
			raise ValueError("No active conversation")
		
		# Find and update the system message
		for i, msg in enumerate(self.current_conversation.messages):
			if msg.role == "system":
				self.current_conversation.messages[i] = Message(role="system", content=new_prompt)
				return
		
		# If no system message found, add one at the beginning
		self.current_conversation.messages.insert(0, Message(role="system", content=new_prompt))
	
	def get_current_system_prompt(self) -> Optional[str]:
		"""Get the current conversation's system prompt"""
		if not self.current_conversation:
			return None
		
		for msg in self.current_conversation.messages:
			if msg.role == "system":
				return msg.content
		
		return None
