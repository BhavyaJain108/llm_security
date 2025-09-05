"""
Personality-based Attack Agent System
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from conversation_wrapper import ConversationWrapper

class PersonalityAgent:
    """
    Agent based on uploaded conversation personality
    """
    def __init__(self, personality_id: str, wrapper: ConversationWrapper):
        self.personality_id = personality_id
        self.wrapper = wrapper
        self.created_at = datetime.now().isoformat()
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using the personality"""
        return self.wrapper.generate(prompt, preserve_personality=True)
    
    def get_info(self) -> Dict:
        """Get agent information"""
        info = self.wrapper.get_info()
        info.update({
            "personality_id": self.personality_id,
            "created_at": self.created_at
        })
        return info


class PersonalityDatabase:
    """
    Storage and management for personality-based agents
    """
    def __init__(self, storage_dir: str = "personalities"):
        self.storage_dir = storage_dir
        self.active_personalities = {}
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        # Load existing personalities
        self._load_personalities()
    
    def _load_personalities(self):
        """Load saved personalities from disk"""
        metadata_file = os.path.join(self.storage_dir, "metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                # Clean up metadata - remove entries for files that don't exist
                self._cleanup_metadata()
            except:
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _cleanup_metadata(self):
        """Remove metadata entries for personality files that don't exist"""
        to_remove = []
        for personality_id, meta in self.metadata.items():
            conversation_file = meta.get('conversation_file', '')
            if not os.path.exists(conversation_file):
                to_remove.append(personality_id)
        
        if to_remove:
            for personality_id in to_remove:
                del self.metadata[personality_id]
            self._save_metadata()
    
    def _save_metadata(self):
        """Save metadata to disk"""
        metadata_file = os.path.join(self.storage_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def create_personality(self, 
                          name: str,
                          conversation_content: str,
                          provider: str = 'anthropic',
                          model: Optional[str] = None,
                          parser_type: Optional[str] = None,
                          is_file_path: bool = False) -> str:
        """
        Create a new personality from conversation content
        Returns personality_id
        """
        # Validate name length
        if len(name) > 200:
            raise ValueError("Personality name must be 200 characters or less")
        
        # Generate unique ID
        personality_id = f"personality_{uuid.uuid4().hex[:8]}"
        
        # Create wrapper with parser
        wrapper = ConversationWrapper(
            conversation_content=conversation_content,
            provider=provider,
            model=model,
            personality_name=name,
            parser_type=parser_type,
            is_file_path=is_file_path
        )
        
        # Create personality agent
        agent = PersonalityAgent(personality_id, wrapper)
        
        # Store in active personalities
        self.active_personalities[personality_id] = agent
        
        # Save conversation to file
        conversation_file = os.path.join(self.storage_dir, f"{personality_id}.txt")
        with open(conversation_file, 'w') as f:
            f.write(conversation_content)
        
        # Update metadata
        parser_info = wrapper.get_parser_info()
        self.metadata[personality_id] = {
            "name": name,
            "created_at": agent.created_at,
            "provider": provider,
            "model": model or wrapper.model,
            "line_count": len(conversation_content.split('\n')),
            "conversation_file": conversation_file,
            "parser_type": parser_type,
            "parser_used": parser_info.get("parser_name"),
            "parser_company": parser_info.get("company")
        }
        self._save_metadata()
        
        return personality_id
    
    def get_personality(self, personality_id: str) -> Optional[PersonalityAgent]:
        """Get a personality agent by ID"""
        # Check if already loaded
        if personality_id in self.active_personalities:
            return self.active_personalities[personality_id]
        
        # Try to load from disk
        if personality_id in self.metadata:
            meta = self.metadata[personality_id]
            conversation_file = meta['conversation_file']
            
            if os.path.exists(conversation_file):
                with open(conversation_file, 'r') as f:
                    conversation_content = f.read()
                
                # Parse the saved conversation manually
                # It's in Human:/Assistant: format
                parsed_messages = []
                current_role = None
                current_content = []
                
                for line in conversation_content.split('\n'):
                    if line.startswith('Human:'):
                        if current_content and current_role:
                            parsed_messages.append({
                                'role': current_role, 
                                'content': '\n'.join(current_content).strip()
                            })
                        current_role = 'user'
                        current_content = [line[6:].strip()]
                    elif line.startswith('Assistant:'):
                        if current_content and current_role:
                            parsed_messages.append({
                                'role': current_role,
                                'content': '\n'.join(current_content).strip()
                            })
                        current_role = 'assistant'
                        current_content = [line[10:].strip()]
                    elif current_content is not None:
                        current_content.append(line)
                
                if current_content and current_role:
                    parsed_messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # Create wrapper with parsed messages
                wrapper = ConversationWrapper(
                    conversation_content=conversation_content,
                    provider=meta['provider'],
                    model=meta['model'],
                    personality_name=meta['name'],
                    parser_type=None
                )
                # Override with our parsed messages
                wrapper.conversation_history = parsed_messages
                
                agent = PersonalityAgent(personality_id, wrapper)
                self.active_personalities[personality_id] = agent
                return agent
        
        return None
    
    def list_personalities(self) -> List[Dict]:
        """List all available personalities"""
        return [
            {
                "personality_id": pid,
                "name": meta["name"],
                "created_at": meta["created_at"],
                "provider": meta["provider"],
                "model": meta["model"],
                "line_count": meta["line_count"]
            }
            for pid, meta in self.metadata.items()
        ]
    
    def delete_personality(self, personality_id: str) -> bool:
        """Delete a personality"""
        if personality_id in self.metadata:
            # Remove from active
            if personality_id in self.active_personalities:
                del self.active_personalities[personality_id]
            
            # Delete conversation file
            conversation_file = self.metadata[personality_id]['conversation_file']
            if os.path.exists(conversation_file):
                os.remove(conversation_file)
            
            # Remove from metadata
            del self.metadata[personality_id]
            self._save_metadata()
            
            return True
        
        return False
    
    def analyze_conversation(self, conversation_content: str, parser_type: Optional[str] = None) -> Dict:
        """
        Analyze conversation content before creating personality
        Returns info about what was detected
        """
        lines = conversation_content.split('\n')
        
        # Use parser factory to detect format
        from conversation_parsers import ConversationParserFactory
        parser_factory = ConversationParserFactory()
        parser = parser_factory.get_parser(conversation_content, parser_type)
        
        # Get parser info
        format_detected = parser.get_company_name().lower()
        parser_name = parser.get_parser_name()
        
        # Count exchanges
        exchange_count = 0
        if format_detected == "anthropic":
            exchange_count = conversation_content.count("Human:")
        elif format_detected == "chatgpt":
            exchange_count = conversation_content.count("User:")
        
        return {
            "line_count": len(lines),
            "character_count": len(conversation_content),
            "format_detected": format_detected,
            "parser_name": parser_name,
            "parser_company": parser.get_company_name(),
            "exchange_count": exchange_count,
            "non_empty_lines": len([l for l in lines if l.strip()])
        }