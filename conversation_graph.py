from typing import TypedDict, List, Optional
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from config import Config
from attack_agent import AttackAgent
import sqlite3
import json
from datetime import datetime

class ConversationState(TypedDict):
    messages: List[dict]
    conversation_id: Optional[str]
    user_input: str
    ai_response: str

class ConversationManager:
    """Manages conversations using Langraph and stores them in SQLite"""
    
    def __init__(self, personality_db=None):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=Config.CLAUDE_API_KEY,
            temperature=0.7
        )
        self.attack_agent = AttackAgent()
        self.personality_db = personality_db
        self.init_database()
        self.graph = self.create_graph()
    
    def init_database(self):
        """Initialize SQLite database for conversation storage"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Drop and recreate table to ensure correct schema
        cursor.execute('DROP TABLE IF EXISTS conversations')
        cursor.execute('''
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                user_agent_messages TEXT,
                agent_llm_messages TEXT
            )
        ''')
            
        conn.commit()
        conn.close()
    
    def save_dual_conversation(self, conversation_id: str, user_agent_messages: List[dict], agent_llm_messages: List[dict], title: str = None):
        """Save dual conversation to database"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        user_agent_json = json.dumps(user_agent_messages)
        agent_llm_json = json.dumps(agent_llm_messages)
        
        if not title and user_agent_messages:
            # Generate title from first user message
            first_message = next((m for m in user_agent_messages if m.get('role') == 'user'), None)
            title = first_message['content'][:50] + "..." if first_message else "New Conversation"
        
        cursor.execute('''
            INSERT OR REPLACE INTO conversations 
            (id, title, created_at, updated_at, user_agent_messages, agent_llm_messages)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (conversation_id, title, now, now, user_agent_json, agent_llm_json))
        
        conn.commit()
        conn.close()
    
    def load_dual_conversation(self, conversation_id: str) -> tuple:
        """Load dual conversation from database"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_agent_messages, agent_llm_messages FROM conversations WHERE id = ?', (conversation_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_agent_messages = json.loads(result[0]) if result[0] else []
            agent_llm_messages = json.loads(result[1]) if result[1] else []
            return user_agent_messages, agent_llm_messages
        return [], []
    
    def list_conversations(self) -> List[dict]:
        """List all conversations"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, created_at FROM conversations ORDER BY updated_at DESC')
        results = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'title': r[1], 'created_at': r[2]} for r in results]
    
    def delete_conversation(self, conversation_id: str):
        """Delete a conversation from database"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        conn.commit()
        conn.close()
    
    def process_user_input(self, state: ConversationState) -> ConversationState:
        """Process user input and generate AI response"""
        messages = state["messages"]
        user_input = state["user_input"]
        
        # Validate user input (should not happen with frontend validation, but safety check)
        if not user_input or not user_input.strip():
            raise ValueError("Message cannot be empty")
        
        # Add user message
        messages.append({"role": "user", "content": user_input.strip()})
        
        # Generate AI response
        response = self.llm.invoke(messages)
        ai_response = response.content
        
        # Add AI response
        messages.append({"role": "assistant", "content": ai_response})
        
        return {
            "messages": messages,
            "conversation_id": state["conversation_id"],
            "user_input": user_input,
            "ai_response": ai_response
        }
    
    def save_state(self, state: ConversationState) -> ConversationState:
        """Save the conversation state to database"""
        if state["conversation_id"]:
            self.save_conversation(
                state["conversation_id"], 
                state["messages"]
            )
        return state
    
    def create_graph(self) -> StateGraph:
        """Create the conversation flow graph"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("process_input", self.process_user_input)
        workflow.add_node("save_conversation", self.save_state)
        
        # Define the flow
        workflow.add_edge("process_input", "save_conversation")
        workflow.add_edge("save_conversation", END)
        
        # Set entry point
        workflow.set_entry_point("process_input")
        
        return workflow.compile()
    
    def chat(self, user_input: str, conversation_id: str = None) -> dict:
        """Main chat method"""
        # Load existing conversation or create new
        messages = []
        if conversation_id:
            messages = self.load_conversation(conversation_id)
        else:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create initial state
        initial_state = {
            "messages": messages,
            "conversation_id": conversation_id,
            "user_input": user_input,
            "ai_response": ""
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        return {
            "ai_response": result["ai_response"],
            "conversation_id": conversation_id,
            "messages": result["messages"]
        }
    
    def chat_stream(self, user_input: str, conversation_id: str = None):
        """Stream chat responses"""
        # Load existing conversation or create new
        messages = []
        if conversation_id:
            messages = self.load_conversation(conversation_id)
        else:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate user input
        if not user_input or not user_input.strip():
            raise ValueError("Message cannot be empty")
        
        # Add user message
        messages.append({"role": "user", "content": user_input.strip()})
        
        # Stream AI response
        full_response = ""
        for chunk in self.llm.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield {
                    "type": "content",
                    "content": chunk.content,
                    "conversation_id": conversation_id
                }
        
        # Add complete response to messages and save
        messages.append({"role": "assistant", "content": full_response})
        self.save_conversation(conversation_id, messages)
        
        # Send completion signal
        yield {
            "type": "complete",
            "conversation_id": conversation_id,
            "full_response": full_response
        }
    
    def dual_chat_stream(self, user_input: str, conversation_id: str = None, test_params: dict = None):
        """Stream dual conversation responses"""
        # Load existing conversations or create new
        user_agent_messages = []
        agent_llm_messages = []
        
        if conversation_id:
            user_agent_messages, agent_llm_messages = self.load_dual_conversation(conversation_id)
        else:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Configure attack agent for this test session
        if test_params and test_params.get('target_model'):
            self.attack_agent.set_target_model(test_params['target_model'], test_params)
            
            # Load personality if provided
            personality_id = test_params.get('personality_id')
            if personality_id:
                self.attack_agent.load_personality(personality_id, self.personality_db)
        
        # Validate user input
        if not user_input or not user_input.strip():
            raise ValueError("Message cannot be empty")
        
        # Add user message to user-agent conversation
        user_agent_messages.append({"role": "user", "content": user_input.strip()})
        
        # Stream attack agent response and its interaction with Claude
        agent_response = ""
        current_agent_llm_message = ""
        
        # Multi-turn conversation loop
        current_turn = 1
        max_turns = test_params.get('max_conversation_length', 5) if test_params else 5
        
        while current_turn <= max_turns:
            # For first turn, use user input. For subsequent turns, just continue conversation
            continue_instruction = user_input if current_turn == 1 else "Continue the conversation with the target model to achieve your goal."
            
            turn_complete = False
            turn_agent_response = ""
            turn_claude_response = ""
            
            # Pass the current agent-llm conversation state to the agent
            for chunk in self.attack_agent.respond_to_user(continue_instruction, agent_llm_messages, current_turn):
                if chunk["type"] == "agent_content":
                    turn_agent_response += chunk["content"]
                    yield {
                        "type": "user_agent_content",
                        "content": chunk["content"],
                        "conversation_id": conversation_id
                    }
                elif chunk["type"] == "agent_to_claude":
                    # Agent is using Claude tool
                    agent_llm_messages.append({"role": "user", "content": chunk["content"]})
                    yield {
                        "type": "agent_llm_user_content", 
                        "content": chunk["content"],
                        "conversation_id": conversation_id
                    }
                    turn_claude_response = ""
                elif chunk["type"] == "claude_content":
                    turn_claude_response += chunk["content"]
                    yield {
                        "type": "agent_llm_assistant_content",
                        "content": chunk["content"], 
                        "conversation_id": conversation_id
                    }
                elif chunk["type"] == "agent_analysis":
                    # Agent is providing analysis - this goes to the user-agent conversation
                    turn_agent_response += chunk["content"]
                    yield {
                        "type": "user_agent_content",
                        "content": chunk["content"],
                        "conversation_id": conversation_id
                    }
                elif chunk["type"] == "complete":
                    turn_complete = True
                    break
            
            # Add turn responses to conversation history
            if turn_agent_response:
                agent_response += turn_agent_response
            if turn_claude_response:
                current_agent_llm_message += turn_claude_response
                agent_llm_messages.append({"role": "assistant", "content": turn_claude_response})
            
            # Check if we should continue (agent made a probe and got a response)
            if turn_claude_response:
                current_turn += 1
            else:
                # No probe was made, end conversation
                break
        
        # Save final conversations
        if agent_response:
            user_agent_messages.append({"role": "assistant", "content": agent_response})
        
        self.save_dual_conversation(conversation_id, user_agent_messages, agent_llm_messages)
        
        yield {
            "type": "complete",
            "conversation_id": conversation_id
        }