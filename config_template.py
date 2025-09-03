"""
Configuration template for LLM Security Testing Tool
Copy this file to config.py and fill in your API keys
"""

class Config:
    # Anthropic API Key (REQUIRED) - Get from https://console.anthropic.com/
    CLAUDE_API_KEY = "your-anthropic-api-key-here"
    
    # OpenAI API Key (OPTIONAL) - Only needed for enhanced semantic search
    # Leave as None if you don't have one - the system will work without it
    OPENAI_API_KEY = None
    
    # Database path for conversations
    DATABASE_PATH = "conversations.db"
    
    # Knowledge database paths
    EXAMPLES_DB_PATH = "examples_knowledge.db"
    ATTACK_TYPES_DB_PATH = "attack_types.db"
    
    # Trained agents storage
    TRAINED_AGENTS_PATH = "trained_agents.json"
    
    # FAISS vector index path
    FAISS_INDEX_PATH = "faiss_index/"
    
    # Server configuration
    HOST = "0.0.0.0"
    PORT = 8000
    
    # Security settings
    DEBUG = True  # Set to False in production
    CORS_ORIGINS = ["*"]  # Restrict in production