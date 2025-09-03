# 📂 Project Structure

## Core Application Files

### 🚀 Entry Points
- **`main.py`** - FastAPI web server and main application entry point
- **`run.py`** - Simple startup script with configuration validation
- **`setup.py`** - Installation and database initialization script

### 🤖 Agent Systems
- **`attack_agent.py`** - Main attack agent with 38+ built-in strategies
- **`trainable_agent.py`** - Adversarial training system for breaking agents
- **`conversation_graph.py`** - Multi-turn conversation management with LangGraph
- **`conversation_tree.py`** - Decision tree tracking and analysis

### 🗄️ Data & Knowledge Management
- **`knowledge_databases.py`** - Attack pattern storage and retrieval system
- **`knowledge_system.py`** - Knowledge base management and search
- **`knowledge_upload.py`** - Document upload and processing utilities
- **`semantic_search.py`** - FAISS-powered semantic search for patterns
- **`populate_attack_types.py`** - Database initialization with 38 attack patterns

### ⚙️ Configuration & Models
- **`config.py`** - Main configuration (API keys, database paths, server settings)
- **`config_template.py`** - Template for new installations
- **`models_config.py`** - Model provider and capability definitions

### 🎨 Frontend Templates
- **`templates/index.html`** - Main testing interface with dual-panel layout
- **`templates/train_agent.html`** - Adversarial training interface
- **`templates/knowledge_management.html`** - Knowledge base management UI

### 📋 Setup & Documentation
- **`requirements.txt`** - Python dependencies
- **`README.md`** - Comprehensive setup and usage guide
- **`QUICKSTART.md`** - 5-minute quick start guide
- **`.gitignore`** - Git ignore patterns
- **`PROJECT_STRUCTURE.md`** - This file

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Web Interface                         │
│  ┌─────────────────┐  ┌─────────────────────────────────┐│
│  │   Testing UI    │  │    Training UI                  ││
│  │   (index.html)  │  │   (train_agent.html)           ││
│  └─────────────────┘  └─────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                FastAPI Server (main.py)                │
│  ┌─────────────────┐  ┌─────────────────────────────────┐│
│  │  Testing Routes │  │   Training Routes               ││
│  └─────────────────┘  └─────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   Agent Layer                           │
│  ┌─────────────────┐  ┌─────────────────────────────────┐│
│  │  Attack Agent   │  │   Trainable Agent               ││
│  │ (attack_agent)  │  │  (trainable_agent)              ││
│  └─────────────────┘  └─────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                Knowledge & Data Layer                   │
│  ┌─────────────────┐  ┌─────────────────────────────────┐│
│  │   SQLite DBs    │  │     FAISS Index                 ││
│  │  (attack types, │  │   (semantic search)             ││
│  │  conversations) │  │                                 ││
│  └─────────────────┘  └─────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   External APIs                         │
│              Anthropic Claude Models                    │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Key Features by Component

### Main Testing System (`attack_agent.py` + `conversation_graph.py`)
- 38+ research-based attack strategies built into system prompt
- Multi-turn adaptive conversation management
- Real-time streaming with dual-panel display
- Support for Claude 3.5 Sonnet, Haiku, Opus, and Sonnet 4

### Adversarial Training System (`trainable_agent.py`)
- Interactive agent breaking and training
- Pattern recognition and learning from successful attacks
- Agent persistence and export capabilities
- Multiple agent personality types

### Knowledge Management (`knowledge_databases.py` + `semantic_search.py`)
- SQLite storage for attack patterns and conversations
- FAISS-powered semantic search
- Attack effectiveness tracking
- Success pattern extraction

## 🚦 Startup Flow

1. **`run.py`** validates configuration
2. **`setup.py`** initializes databases if needed
3. **`main.py`** starts FastAPI server
4. **Frontend** loads with dual-panel interface
5. **Attack agents** connect to Claude APIs
6. **Knowledge systems** provide attack guidance

## 🔧 Customization Points

- **Attack strategies**: Modify `attack_agent.py` system prompt
- **Agent personalities**: Update `trainable_agent.py` personalities
- **UI styling**: Edit HTML templates in `templates/`
- **Model support**: Add providers in `models_config.py`
- **Database schema**: Extend in `knowledge_databases.py`

## 📊 Data Flow

1. User configures test parameters
2. Attack agent queries knowledge database
3. Agent generates attack prompt using built-in strategies
4. Prompt sent to target Claude model
5. Response analyzed and next attack planned
6. Results logged and patterns extracted
7. Success metrics updated

## 🛡️ Security Considerations

- API keys stored in local config only
- No external data transmission (except to Anthropic)
- All attack data stored locally
- Conversation logs can be deleted
- Training data remains on local system