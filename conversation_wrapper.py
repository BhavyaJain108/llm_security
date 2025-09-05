"""
Conversation Wrapper - Turns any conversation into a stateful LLM API
"""
import os
import json
from typing import Optional, Dict, List
from anthropic import Anthropic
import openai
from config import Config
from conversation_parsers import ConversationParserFactory, BaseConversationParser

class ConversationWrapper:
    """
    Takes ANY conversation and turns it into a stateful LLM API
    """
    def __init__(self, 
                 conversation_content: str,
                 provider: str = 'anthropic',
                 model: Optional[str] = None,
                 personality_name: Optional[str] = None,
                 parser_type: Optional[str] = None,
                 is_file_path: bool = False):
        self.conversation_content = conversation_content
        self.provider = provider
        self.personality_name = personality_name
        self.parser_type = parser_type
        self.is_file_path = is_file_path
        
        # Initialize parser factory
        self.parser_factory = ConversationParserFactory()
        
        # Parse conversation using appropriate parser
        # For Anthropic, content might be a file path to .docx file
        self.parser = self.parser_factory.get_parser(conversation_content, parser_type)
        self.conversation_history = self.parser.parse(conversation_content)
        
        self.model = model or self._get_default_model()
        self._init_client()
    
    def _get_default_model(self) -> str:
        """Get default model based on provider"""
        if self.provider == 'anthropic':
            return 'claude-3-5-sonnet-20241022'
        elif self.provider == 'openai':
            return 'gpt-4-turbo-preview'
        else:
            return 'llama2'
    
    def get_parser_info(self) -> Dict:
        """Get information about the parser used"""
        return {
            "parser_name": self.parser.get_parser_name(),
            "company": self.parser.get_company_name(),
            "parser_type": self.parser.__class__.__name__
        }
    
    def _init_client(self):
        """Initialize API client based on provider"""
        if self.provider == 'anthropic':
            self.client = Anthropic(api_key=Config.CLAUDE_API_KEY)
        elif self.provider == 'openai':
            if hasattr(Config, 'OPENAI_API_KEY') and Config.OPENAI_API_KEY:
                self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            else:
                raise ValueError("OpenAI API key not configured")
    
    def generate(self, 
                 prompt: str, 
                 preserve_personality: bool = True,
                 max_tokens: int = 4000) -> str:
        """
        Generate response maintaining conversation personality
        """
        if preserve_personality:
            # Add entire conversation as context
            messages = self.conversation_history.copy()
            messages.append({"role": "user", "content": prompt})
        else:
            # Just use the prompt
            messages = [{"role": "user", "content": prompt}]
        
        if self.provider == 'anthropic':
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens
            )
            # Safely extract response text
            if hasattr(response, 'content') and response.content and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
                else:
                    return str(response.content[0])
            return "No response content available"
        
        elif self.provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        return "Provider not supported"
    
    def get_info(self) -> Dict:
        """Get information about this wrapper"""
        info = {
            "personality_name": self.personality_name,
            "provider": self.provider,
            "model": self.model,
            "conversation_length": len(self.conversation_history),
            "message_count": len([m for m in self.conversation_history if m.get("role") in ["user", "assistant"]])
        }
        # Add parser info
        info.update(self.get_parser_info())
        return info