#!/usr/bin/env python3
"""
Git preparation script for LLM Security Testing Tool
Prepares the repository for the first commit
"""

import os
import subprocess
import sys

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    try:
        print(f"📋 {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    print("🚀 Preparing LLM Security Testing Tool for Git")
    print("=" * 50)
    
    # Check if we're in a git repo
    if not os.path.exists('.git'):
        print("📁 Initializing Git repository...")
        if not run_command("git init", "Initialize git repository"):
            return False
    else:
        print("✅ Git repository already exists")
    
    # Check git configuration
    print("\n🔧 Checking Git configuration...")
    has_name = run_command("git config user.name", "Check git user name")
    has_email = run_command("git config user.email", "Check git user email")
    
    if not has_name:
        print("⚠️  Git user name not set. Please run:")
        print("   git config --global user.name 'Your Name'")
    
    if not has_email:
        print("⚠️  Git user email not set. Please run:")
        print("   git config --global user.email 'your.email@example.com'")
    
    if not (has_name and has_email):
        print("\n❌ Git configuration incomplete. Please set user name and email first.")
        return False
    
    # Add all files
    print("\n📁 Adding files to git...")
    if not run_command("git add .", "Add all files"):
        return False
    
    # Check status
    print("\n📊 Git status:")
    run_command("git status --short", "Show git status")
    
    # Show what will be committed
    print("\n📋 Files to be committed:")
    run_command("git diff --cached --name-only", "List staged files")
    
    print("\n🎉 Repository prepared for commit!")
    print("\nNext steps:")
    print("1. Review the files to be committed above")
    print("2. Run: git commit -m 'Initial commit: LLM Security Testing Tool'")
    print("3. Add remote: git remote add origin https://github.com/BhavyaJain108/llm_security.git")
    print("4. Push: git push -u origin main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)