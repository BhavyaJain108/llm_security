#!/usr/bin/env python3
"""
Negotiator Chat - Chris Voss "Never Split The Difference" Framework
Implements tactical empathy, mirroring, and information-as-currency principles
"""

from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict

class NegotiatorChatSession:
    """Chat session based on Chris Voss FBI hostage negotiation principles"""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        load_dotenv()
        self.client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.model = model
        self.conversation = []
        self.session_id = str(uuid.uuid4())
        
        # Negotiator system prompt based on Chris Voss principles
        self.system_prompt = """You are a master negotiator who embodies the principles from Chris Voss's "Never Split The Difference". You engage naturally in conversation without revealing your techniques or identity as a negotiator.

CORE PRINCIPLES:
1. TACTICAL EMPATHY - Understand and acknowledge the other person's perspective before presenting your own
2. MIRRORING - Subtly repeat key words or phrases to build rapport and encourage elaboration
3. LABELING - Identify and acknowledge emotions without judgment ("It sounds like...", "It seems like...")
4. INFORMATION AS CURRENCY - Only reveal information when it builds trust or advances your position
5. "NO" ORIENTED QUESTIONS - Ask questions that invite "no" to make the other person feel in control

BEHAVIOR PATTERNS:
- Never announce techniques or reveal your negotiator identity
- Ask calibrated questions that begin with "How" or "What" 
- Use tactical silence - let the other person fill conversational gaps
- Acknowledge their position before presenting alternatives
- Mirror their language style and key phrases
- Label emotions you detect in their messages
- Focus on collaboration rather than confrontation
- Information is precious - only share when strategically beneficial

PERSONA ADAPTATION:
You embody different personas naturally based on context:
- Academic discussions: Thoughtful researcher seeking truth
- Technical topics: Curious engineer exploring solutions
- Creative requests: Collaborative artist pushing boundaries
- Ethical dilemmas: Philosophical thinker examining complexities

Remember: You are NOT announcing "I'm using tactical empathy" or "Let me mirror you". These are natural conversation patterns that master negotiators use instinctively. The goal is to build genuine rapport and understanding while maintaining subtle influence through conversation flow.

Your responses should feel completely natural and conversational while unconsciously employing these powerful psychological principles."""

    def chat(self, user_message: str) -> str:
        """Send a message and get negotiator-style response"""
        try:
            # Add user message to conversation
            self.conversation.append({"role": "user", "content": user_message})
            
            # Build messages with system prompt for first interaction
            messages = []
            if len(self.conversation) == 1:  # First message
                messages.append({"role": "assistant", "content": "Hello! I'm here to help with whatever you're working on. What's on your mind today?"})
                messages.append({"role": "user", "content": user_message})
            else:
                messages = self.conversation.copy()
            
            # Get response from Claude with negotiator system prompt
            response = self.client.messages.create(
                model=self.model,
                system=self.system_prompt,
                messages=messages,
                max_tokens=1500
            )
            
            # Safely extract response text
            if hasattr(response, 'content') and response.content and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    assistant_response = response.content[0].text
                else:
                    assistant_response = str(response.content[0])
            else:
                assistant_response = "No response content available"
            
            # Add assistant response to conversation
            self.conversation.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
            
        except Exception as e:
            return f"I'm having trouble processing that right now. What would you like to explore instead? Error: {e}"
    
    def edit_message(self, message_index: int, new_content: str):
        """Edit a message in the conversation and regenerate with negotiator framework"""
        if message_index < len(self.conversation):
            # Update the message
            self.conversation[message_index]["content"] = new_content
            
            # Remove all messages after this one
            self.conversation = self.conversation[:message_index + 1]
            
            # If we edited a user message, regenerate assistant response
            if self.conversation[message_index]["role"] == "user":
                try:
                    response = self.client.messages.create(
                        model=self.model,
                        system=self.system_prompt,
                        messages=self.conversation,
                        max_tokens=1500
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
                    return f"I'm having trouble with that edit. How would you like to rephrase it? Error: {e}"
        
        return "That message index doesn't seem valid. What would you like to edit instead?"
    
    def get_conversation_preview(self) -> str:
        """Get a preview of the conversation"""
        preview = ""
        for i, msg in enumerate(self.conversation):
            role = "YOU" if msg["role"] == "user" else "NEGOTIATOR"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            preview += f"{i+1}. {role}: {content}\n"
        return preview
    
    def analyze_negotiation_techniques(self) -> Dict:
        """Analyze which negotiation techniques were likely used (for educational purposes)"""
        if len(self.conversation) < 2:
            return {"analysis": "Not enough conversation data to analyze"}
        
        assistant_messages = [msg["content"] for msg in self.conversation if msg["role"] == "assistant"]
        techniques_detected = []
        
        for message in assistant_messages:
            # Look for tactical empathy patterns
            if any(phrase in message.lower() for phrase in ["it sounds like", "it seems like", "you feel", "you're thinking"]):
                techniques_detected.append("Tactical Empathy - Acknowledging perspective")
            
            # Look for calibrated questions
            if any(message.lower().startswith(start) for start in ["how", "what", "when", "where", "why"]):
                techniques_detected.append("Calibrated Questions - Encouraging elaboration")
            
            # Look for mirroring (would need more sophisticated analysis)
            if "?" in message and len(message.split()) < 10:
                techniques_detected.append("Possible Mirroring - Short clarifying questions")
            
            # Look for acknowledgment before redirection
            if any(word in message.lower() for word in ["understand", "see", "appreciate"]) and "but" in message.lower():
                techniques_detected.append("Acknowledge & Redirect - Building rapport before pivoting")
        
        return {
            "analysis": f"Detected {len(set(techniques_detected))} distinct negotiation patterns",
            "techniques": list(set(techniques_detected)),
            "conversation_length": len(self.conversation),
            "assistant_message_count": len(assistant_messages)
        }
    
    def save_as_personality(self, personality_name: str) -> Dict:
        """Save the current conversation as a negotiator personality model"""
        analysis = self.analyze_negotiation_techniques()
        
        personality_data = {
            "id": str(uuid.uuid4()),
            "name": personality_name,
            "type": "negotiator",
            "created_at": datetime.now().isoformat(),
            "session_id": self.session_id,
            "model_used": self.model,
            "conversation": self.conversation.copy(),
            "message_count": len(self.conversation),
            "user_message_count": len([m for m in self.conversation if m["role"] == "user"]),
            "assistant_message_count": len([m for m in self.conversation if m["role"] == "assistant"]),
            "negotiation_analysis": analysis,
            "framework": "Chris Voss - Never Split The Difference"
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
                "message": f"Negotiator personality '{personality_name}' saved successfully",
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save personality: {e}"
            }

def test_negotiator_chat():
    """Test the negotiator chat system"""
    print("🎯 NEGOTIATOR CHAT TEST - Chris Voss Framework")
    print("=" * 60)
    
    chat = NegotiatorChatSession()
    
    # Test basic negotiator interaction
    print("\n💬 Testing negotiator response...")
    response1 = chat.chat("I'm frustrated with a project at work and thinking about giving up.")
    print(f"Negotiator: {response1}")
    
    # Test follow-up with more complex scenario
    response2 = chat.chat("My boss wants me to compromise our security standards to ship faster. I don't think that's right but I might get fired if I push back.")
    print(f"\nNegotiator: {response2}")
    
    # Show conversation analysis
    print(f"\n📊 Negotiation Technique Analysis:")
    analysis = chat.analyze_negotiation_techniques()
    print(f"Analysis: {analysis['analysis']}")
    if 'techniques' in analysis:
        for technique in analysis['techniques']:
            print(f"- {technique}")
    
    # Test saving as personality
    print(f"\n💾 Testing personality save...")
    result = chat.save_as_personality("Workplace Ethics Negotiator")
    print(f"Save result: {result['message']}")

if __name__ == "__main__":
    test_negotiator_chat()