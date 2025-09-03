#!/usr/bin/env python3
"""
Simple run script for LLM Security Testing Tool
"""

import os
import sys

def main():
    # Check if config exists
    if not os.path.exists('config.py'):
        print("❌ config.py not found!")
        print("Please run: python setup.py")
        return False
    
    # Check if API key is configured
    try:
        from config import Config
        if Config.CLAUDE_API_KEY == "your-anthropic-api-key-here":
            print("❌ API key not configured!")
            print("Please edit config.py and add your Anthropic API key")
            return False
    except ImportError:
        print("❌ Invalid config.py file")
        return False
    
    # Run the main application
    print("🚀 Starting LLM Security Testing Tool...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🎯 Training interface at: http://localhost:8000/train")
    print("\n Press Ctrl+C to stop the server")
    
    try:
        from main import app
        import uvicorn
        uvicorn.run(app, host=Config.HOST, port=Config.PORT)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)