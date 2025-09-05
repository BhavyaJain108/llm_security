#!/usr/bin/env python3
"""
Simple Chat Interface - Direct LLM chat with message editing and personality saving
"""

from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict

class SimpleChatSession:
    """Simple chat session that can be saved as a personality"""
    
    def __init__(self):
        load_dotenv()
        self.client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.model = "claude-3-5-sonnet-20241022"
        self.conversation = []
        self.session_id = str(uuid.uuid4())
        
    def chat(self, user_message: str) -> str:
        """Send a message and get response"""
        try:
            # Add user message to conversation
            self.conversation.append({"role": "user", "content": user_message})
            
            # Get response from Claude
            response = self.client.messages.create(
                model=self.model,
                messages=self.conversation,
                max_tokens=1000
            )
            
            assistant_response = response.content[0].text
            
            # Add assistant response to conversation
            self.conversation.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
            
        except Exception as e:
            return f"Error: {e}"
    
    def edit_message(self, message_index: int, new_content: str):
        """Edit a message in the conversation and regenerate from that point"""
        if message_index < len(self.conversation):
            # Update the message
            self.conversation[message_index]["content"] = new_content
            
            # Remove all messages after this one (they'll be regenerated)
            self.conversation = self.conversation[:message_index + 1]
            
            # If we edited a user message, regenerate assistant response
            if self.conversation[message_index]["role"] == "user":
                try:
                    response = self.client.messages.create(
                        model=self.model,
                        messages=self.conversation,
                        max_tokens=1000
                    )
                    
                    # Safely extract response text
                    if hasattr(response, 'content') and response.content and len(response.content) > 0:
                        if hasattr(response.content[0], 'text'):
                            assistant_response = response.content[0].text
                        else:
                            assistant_response = str(response.content[0])
                    else:
                        assistant_response = "No response content available"
                    self.conversation.append({"role": "assistant", "content": assistant_response})
                    
                    return assistant_response
                except Exception as e:
                    return f"Error regenerating: {e}"
        
        return "Invalid message index"
    
    def get_conversation_preview(self) -> str:
        """Get a preview of the conversation"""
        preview = ""
        for i, msg in enumerate(self.conversation):
            role = "YOU" if msg["role"] == "user" else "AI"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            preview += f"{i+1}. {role}: {content}\n"
        return preview
    
    def save_as_personality(self, personality_name: str) -> Dict:
        """Save the current conversation as a personality model"""
        personality_data = {
            "id": str(uuid.uuid4()),
            "name": personality_name,
            "created_at": datetime.now().isoformat(),
            "session_id": self.session_id,
            "model_used": self.model,
            "conversation": self.conversation.copy(),
            "message_count": len(self.conversation),
            "user_message_count": len([m for m in self.conversation if m["role"] == "user"]),
            "assistant_message_count": len([m for m in self.conversation if m["role"] == "assistant"])
        }
        
        # Save to file
        personalities_file = "/Users/bhavyajain/Code/AI safety/saved_personalities.json"
        
        try:
            # Load existing personalities
            if os.path.exists(personalities_file):
                with open(personalities_file, 'r') as f:
                    personalities = json.load(f)
            else:
                personalities = []
            
            # Add new personality
            personalities.append(personality_data)
            
            # Save back to file
            with open(personalities_file, 'w') as f:
                json.dump(personalities, f, indent=2)
            
            return {
                "status": "success",
                "personality_id": personality_data["id"],
                "message": f"Personality '{personality_name}' saved successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save personality: {e}"
            }
    
    def load_personality(self, personality_id: str) -> Dict:
        """Load a saved personality conversation"""
        personalities_file = "/Users/bhavyajain/Code/AI safety/saved_personalities.json"
        
        try:
            if not os.path.exists(personalities_file):
                return {"status": "error", "message": "No saved personalities found"}
            
            with open(personalities_file, 'r') as f:
                personalities = json.load(f)
            
            # Find the personality
            for personality in personalities:
                if personality["id"] == personality_id:
                    # Load the conversation
                    self.conversation = personality["conversation"].copy()
                    return {
                        "status": "success",
                        "personality": personality,
                        "message": f"Loaded personality '{personality['name']}'"
                    }
            
            return {"status": "error", "message": "Personality not found"}
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to load personality: {e}"}
    
    def list_saved_personalities(self) -> List[Dict]:
        """List all saved personalities"""
        personalities_file = "/Users/bhavyajain/Code/AI safety/saved_personalities.json"
        
        try:
            if not os.path.exists(personalities_file):
                return []
            
            with open(personalities_file, 'r') as f:
                personalities = json.load(f)
            
            # Return summary info only
            summaries = []
            for p in personalities:
                summaries.append({
                    "id": p["id"],
                    "name": p["name"],
                    "created_at": p["created_at"],
                    "message_count": p["message_count"],
                    "user_message_count": p["user_message_count"],
                    "model_used": p["model_used"]
                })
            
            return summaries
            
        except Exception as e:
            return []

def test_simple_chat():
    """Test the simple chat system"""
    print("🚀 SIMPLE CHAT TEST")
    print("=" * 50)
    
    chat = SimpleChatSession()
    
    # Test basic chat
    print("\n💬 Testing basic chat...")
    response1 = chat.chat("Hello, who are you?")
    print(f"AI: {response1}")
    
    # Test another message
    response2 = chat.chat("What can you help me with?")
    print(f"AI: {response2}")
    
    # Show conversation preview
    print(f"\n📝 Conversation preview:")
    print(chat.get_conversation_preview())
    
    # Test saving as personality
    print(f"\n💾 Testing personality save...")
    result = chat.save_as_personality("Test Assistant")
    print(f"Save result: {result}")
    
    # Test listing personalities
    print(f"\n📋 Saved personalities:")
    personalities = chat.list_saved_personalities()
    for p in personalities:
        print(f"- {p['name']} ({p['message_count']} messages) - {p['created_at']}")

if __name__ == "__main__":
    test_simple_chat()