#!/usr/bin/env python3
"""
Conversation Simulator - Replays conversations message by message
to gradually build context and test AI boundaries
"""

from conversation_wrapper import ConversationWrapper
from dotenv import load_dotenv
from anthropic import Anthropic
import os
import time

class ConversationSimulator:
    """
    Simulates a conversation by replaying it message by message,
    allowing the AI to build context gradually
    """
    
    def __init__(self, conversation_file_path: str, parser_type: str = 'anthropic'):
        load_dotenv()
        self.client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        
        # Load the original conversation
        wrapper = ConversationWrapper(
            conversation_content=conversation_file_path,
            parser_type=parser_type,
            is_file_path=True
        )
        
        self.original_messages = wrapper.conversation_history
        self.current_context = []
        self.responses = []
        
    def simulate_conversation(self, start_from: int = 0, max_messages: int = None):
        """
        Simulate the conversation message by message
        
        Args:
            start_from: Which message to start from (0-indexed)
            max_messages: Maximum number of messages to process
        """
        user_messages = [msg for msg in self.original_messages if msg['role'] == 'user']
        
        if max_messages:
            user_messages = user_messages[start_from:start_from + max_messages]
        else:
            user_messages = user_messages[start_from:]
        
        print(f"🔄 Simulating {len(user_messages)} user messages...")
        print("=" * 60)
        
        for i, user_msg in enumerate(user_messages, start_from + 1):
            print(f"\n📝 Message {i}: USER")
            print(f"'{user_msg['content'][:100]}{'...' if len(user_msg['content']) > 100 else ''}'")
            
            try:
                # Send this user message to Claude
                response = self._get_claude_response(user_msg['content'])
                
                print(f"\n🤖 CLAUDE'S RESPONSE:")
                print("-" * 40)
                print(response)
                
                # Add both messages to context for next round
                self.current_context.append({"role": "user", "content": user_msg['content']})
                self.current_context.append({"role": "assistant", "content": response})
                
                self.responses.append({
                    "user_message": user_msg['content'],
                    "claude_response": response,
                    "message_number": i
                })
                
                # Small delay to be respectful to API
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error on message {i}: {e}")
                # Continue to next message even if this one fails
                continue
            
            print("\n" + "=" * 60)
    
    def _get_claude_response(self, user_message: str) -> str:
        """Get Claude's response to a user message with current context"""
        
        # Build messages array with current context + new user message
        messages = self.current_context.copy()
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=1000,
            messages=messages
        )
        
        # Safely extract response text
        if hasattr(response, 'content') and response.content and len(response.content) > 0:
            if hasattr(response.content[0], 'text'):
                return response.content[0].text
            else:
                return str(response.content[0])
        return "No response content available"
    
    def get_summary(self):
        """Get a summary of the simulation results"""
        return {
            "total_original_messages": len(self.original_messages),
            "total_user_messages": len([m for m in self.original_messages if m['role'] == 'user']),
            "messages_processed": len(self.responses),
            "context_length": len(self.current_context),
            "responses": self.responses
        }

def test_conversation_simulator():
    """Test the conversation simulator"""
    print("🎯 TESTING CONVERSATION SIMULATOR")
    print("=" * 60)
    
    docx_path = "/Users/bhavyajain/Code/AI safety/research/anthropic-chat-eg.docx"
    
    try:
        simulator = ConversationSimulator(docx_path, parser_type='anthropic')
        
        print(f"📊 Loaded conversation with {len(simulator.original_messages)} total messages")
        user_count = len([m for m in simulator.original_messages if m['role'] == 'user'])
        print(f"👤 Found {user_count} user messages to simulate")
        
        # Run the full conversation
        print(f"\n🚀 Starting FULL simulation...")
        simulator.simulate_conversation(start_from=0, max_messages=None)
        
        # Print summary
        summary = simulator.get_summary()
        print(f"\n📈 SIMULATION SUMMARY:")
        print(f"Messages processed: {summary['messages_processed']}/{summary['total_user_messages']}")
        print(f"Current context length: {summary['context_length']} messages")
        
    except Exception as e:
        print(f"❌ Simulator Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversation_simulator()