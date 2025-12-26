#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        print(f"Command: {cmd}")
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    print("🚀 Starting deployment process...")
    
    # Check if we're in a git repo
    if not os.path.exists('.git'):
        print("❌ Not a git repository!")
        return
    
    # Add files
    print("\n📝 Adding files...")
    if not run_command('git add bot.py prayer_config.json'):
        print("⚠️ Failed to add files")
        return
    
    # Commit
    print("\n💾 Committing changes...")
    commit_msg = "Add greeting reply and fix prayer config"
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("⚠️ Failed to commit (maybe no changes?)")
    
    # Push
    print("\n⬆️ Pushing to remote...")
    if not run_command('git push'):
        print("❌ Failed to push")
        print("⚠️ Please check your git remote configuration")
        return
    
    print("\n✅ Deployment complete! Railway should auto-deploy soon.")

if __name__ == "__main__":
    main()

