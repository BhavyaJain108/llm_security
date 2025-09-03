#!/usr/bin/env python3
"""
Setup script for LLM Security Testing Tool
Run this after installing requirements to initialize the system
"""

import os
import sys
import shutil

def main():
    print("🛡️ LLM Security Testing Tool Setup")
    print("=" * 40)
    
    # Check if config exists
    if not os.path.exists('config.py'):
        if os.path.exists('config_template.py'):
            print("📝 Creating config.py from template...")
            shutil.copy('config_template.py', 'config.py')
            print("✅ config.py created!")
            print("⚠️  Please edit config.py and add your Anthropic API key")
        else:
            print("❌ config_template.py not found!")
            return False
    else:
        print("✅ config.py already exists")
    
    # Initialize databases
    print("\n🗄️ Initializing databases...")
    try:
        # Run the population script
        if os.path.exists('populate_attack_types.py'):
            import subprocess
            result = subprocess.run([sys.executable, 'populate_attack_types.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Attack types database initialized")
                print(result.stdout)
            else:
                print("❌ Error initializing database:")
                print(result.stderr)
        
        # Create other database files
        try:
            from knowledge_databases import KnowledgeDatabases
            kb = KnowledgeDatabases()
            print("✅ Knowledge databases initialized")
        except ImportError as e:
            print(f"⚠️  Optional dependency missing: {e}")
            print("   Semantic search features may be limited")
            print("   Install with: pip install faiss-cpu sentence-transformers")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False
    
    # Create directories
    print("\n📁 Creating directories...")
    directories = ['static', 'templates', 'faiss_index']
    for dir_name in directories:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ Created {dir_name}/")
        else:
            print(f"✅ {dir_name}/ already exists")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit config.py and add your Anthropic API key")
    print("2. Run: python main.py")
    print("3. Open: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)