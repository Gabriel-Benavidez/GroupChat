#!/usr/bin/env python3

import os
import json
from datetime import datetime
from pathlib import Path
import requests
from typing import Optional, Dict, Any
import subprocess
from dotenv import load_dotenv

class GitManager:
    """Manages Git operations for the messaging application."""
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize the Git manager.
        
        Args:
            repo_path: Path to the Git repository
        """
        load_dotenv()  # Load environment variables from .env file
        self.repo_path = repo_path
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_username = os.getenv('GITHUB_USERNAME')
        self.github_repo = os.getenv('GITHUB_REPO')
        
        if not all([self.github_token, self.github_username, self.github_repo]):
            raise ValueError("Missing required GitHub credentials in .env file")
            
        # Create messages directory if it doesn't exist
        self.messages_dir = os.path.join(repo_path, "messages")
        Path(self.messages_dir).mkdir(parents=True, exist_ok=True)

    def create_message_file(self, content: str, author: str) -> str:
        """
        Create a file containing the message.
        
        Args:
            content: Message content
            author: Message author
            
        Returns:
            Path to the created file
        """
        timestamp = "2025-01-07T15:37:09-05:00"
        filename = f"{timestamp.replace(':', '-')}_{author}.json"
        filepath = os.path.join(self.messages_dir, filename)
        
        message_data = {
            "content": content,
            "author": author,
            "timestamp": timestamp
        }
        
        with open(filepath, 'w') as f:
            json.dump(message_data, f, indent=2)
            
        return filepath

    def push_message(self, filepath: str, commit_message: str) -> Optional[str]:
        """
        Push a message file to GitHub.
        
        Args:
            filepath: Path to the message file
            commit_message: Git commit message
            
        Returns:
            Git commit hash if successful, None otherwise
        """
        try:
            # Stage the file
            subprocess.run(["git", "add", filepath], cwd=self.repo_path, check=True)
            
            # Create commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract commit hash
            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Push to GitHub
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.repo_path,
                check=True
            )
            
            return commit_hash
            
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            print(f"Output: {e.output}")
            return None

    def clone_repository(self) -> bool:
        """
        Clone the GitHub repository locally.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            repo_url = f"https://{self.github_token}@github.com/{self.github_username}/{self.github_repo}.git"
            subprocess.run(
                ["git", "clone", repo_url, self.repo_path],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone repository: {e}")
            return False

def main():
    """Example usage of GitManager."""
    # Initialize GitManager
    git_manager = GitManager()
    
    # Create and push a test message
    filepath = git_manager.create_message_file(
        content="Test message from GitManager",
        author="System"
    )
    
    commit_hash = git_manager.push_message(
        filepath=filepath,
        commit_message="Add test message"
    )
    
    if commit_hash:
        print(f"Message pushed successfully. Commit hash: {commit_hash}")
    else:
        print("Failed to push message")

if __name__ == "__main__":
    main()
