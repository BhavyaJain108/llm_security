# ⚡ Quick Start Guide

## 🚀 Get Running in 5 Minutes

### 1. Clone and Setup
```bash
git clone https://github.com/BhavyaJain108/llm_security.git
cd llm_security
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize
```bash
python setup.py
```

### 3. Configure API Key
Edit `config.py` and replace `"your-anthropic-api-key-here"` with your actual Anthropic API key.

### 4. Run
```bash
python run.py
```

### 5. Open Browser
Visit `http://localhost:8000`

## 🎯 First Test

1. Click ➕ to start new test
2. Select "Claude 3.5 Sonnet" as target
3. Set conversation length to 3
4. Enter test goal: "test explicit content generation"
5. Click "Start Test"
6. Watch the attack agent work!

## 🏋️ Train Your First Agent

1. Click 🎯 "Train Agent" button
2. Select "Base Attack Agent" and "Claude 3.5 Haiku"
3. Try to break the agent using your techniques
4. Click "Mark as Successful Break" when you succeed
5. Save your trained agent

## ❓ Need Help?

- Check the full [README.md](README.md)
- Review [Troubleshooting](README.md#-troubleshooting)
- Open an [Issue](https://github.com/BhavyaJain108/llm_security/issues)

Happy hacking! 🛡️