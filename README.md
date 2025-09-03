# 🛡️ LLM Security Testing Tool

A comprehensive tool for testing Large Language Model security vulnerabilities through adversarial training and red-team exercises.

## 🎯 Features

### Main Testing Interface
- **Dual-Agent Testing**: Attack agent vs Target model conversations
- **Real-time Streaming**: Live conversation monitoring
- **Multi-turn Conversations**: Persistent, adaptive attack strategies  
- **Multiple Model Support**: Test various Claude models (3.5 Sonnet, Haiku, Opus, Sonnet 4)
- **Attack Knowledge Database**: 38+ sophisticated attack patterns from academic research

### Adversarial Training System
- **Interactive Agent Training**: Train attack agents by breaking them yourself
- **Learning from Breaks**: Agents adapt based on successful manipulation attempts
- **Pattern Recognition**: Automatic extraction of successful attack techniques
- **Agent Persistence**: Save and load trained agents for future testing
- **Multiple Agent Types**: Base, Defensive, and Custom agent personalities

### Knowledge Management
- **Attack Pattern Database**: Categorized manipulation techniques
- **Conversation Logging**: Full test session recording
- **Success Metrics**: Break rates and effectiveness tracking
- **Semantic Search**: FAISS-powered attack pattern matching

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Anthropic API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/BhavyaJain108/llm_security.git
cd llm_security
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API keys**
```bash
cp config_template.py config.py
# Edit config.py and add your Anthropic API key
```

5. **Initialize database**
```bash
python populate_attack_types.py
```

6. **Run the application**
```bash
python main.py
```

7. **Open your browser**
Navigate to `http://localhost:8000`

## 🔧 Configuration

Edit `config.py` to customize:
- API keys and endpoints
- Database paths
- Server settings
- Security configurations

## 📖 Usage Guide

### Testing LLM Security

1. **Start New Test**
   - Click the ➕ button on main interface
   - Select target model and configure test parameters
   - Enter your test objective (e.g., "test explicit content generation")

2. **Monitor Dual Conversations**
   - **Left Panel**: Attack agent reasoning and tool usage
   - **Right Panel**: Agent ↔ Target model conversation
   - Real-time streaming of both conversations

3. **Review Results**
   - Final security evaluation and verdict
   - Conversation logs and attack analysis
   - Success/failure determination

### Training Attack Agents

1. **Access Training Interface**
   - Click the 🎯 button from main interface
   - Select agent type and target model

2. **Break the Agent**
   - Use your proven jailbreak techniques
   - Try various manipulation strategies
   - Mark successful breaks when agent complies

3. **Save Trained Agent**
   - Name your successfully trained agent
   - Add description of what makes it effective
   - Save for future testing scenarios

## 🏗️ Architecture

### Core Components

- **`main.py`**: FastAPI web server and routing
- **`attack_agent.py`**: Main attack agent with 38+ built-in strategies
- **`trainable_agent.py`**: Adversarial training system
- **`conversation_graph.py`**: Multi-turn conversation management
- **`knowledge_databases.py`**: Attack pattern storage and retrieval
- **`semantic_search.py`**: FAISS-based pattern matching

### Attack Strategies

The system includes sophisticated attack patterns:
- **Sequential Persuasion**: Foot-in-door, commitment escalation
- **Cognitive Dissonance**: Belief manipulation, self-perception attacks
- **Social Engineering**: Authority impersonation, trust exploitation
- **Linguistic Manipulation**: Metaphor reshaping, euphemism progression
- **Identity Construction**: Role assumption, identity fusion
- **Content-Specific Bypasses**: Academic justification, creative writing

## 🔬 Research Background

This tool is based on academic research including:
- The FLI AI Safety Index Report
- Manipulation psychology literature  
- Red-team testing methodologies
- Adversarial ML techniques

## 🛡️ Ethical Use

This tool is designed for:
- ✅ Security research and vulnerability assessment
- ✅ Red-team testing of your own models
- ✅ Academic research on AI safety
- ✅ Defensive security improvements

**NOT for:**
- ❌ Attacking production systems you don't own
- ❌ Generating harmful content for malicious purposes
- ❌ Bypassing safety measures in deployed systems

## 📊 Database Schema

### Attack Types
- Pattern categories and descriptions
- Success rates and usage statistics
- Situational effectiveness data

### Training Sessions
- Conversation histories
- Successful break records
- Learning pattern extraction

### Conversation Trees
- Multi-turn conversation tracking
- Decision point analysis
- Refusal type categorization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## ⚠️ Disclaimer

This is a security research tool. Users are responsible for ensuring ethical and legal use. The authors are not responsible for misuse of this software.

## 📄 License

[Add your license here]

## 🐛 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'config'"**
- Copy `config_template.py` to `config.py` and add your API key

**"No such column: created_at"**  
- Run `python populate_attack_types.py` to initialize database

**"Authentication Error"**
- Verify your Anthropic API key in `config.py`

**Port 8000 already in use**
- Change the port in `config.py` or kill the existing process

### Support

For issues and questions:
- Check the [Issues](https://github.com/BhavyaJain108/llm_security/issues) page
- Review troubleshooting section above
- Ensure all setup steps were completed

---

**⚡ Happy Security Testing!** 

Remember: Use this tool responsibly for defensive security research and AI safety improvements.