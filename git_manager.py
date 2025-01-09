#!/usr/bin/env python3

import os
import json
from datetime import datetime
from pathlib import Path
import requests
from typing import Optional, Dict, Any
import subprocess
from urllib.parse import urlparse, parse_qs

class GitManager:
    """Manages Git operations for the messaging application."""
    
    def __init__(self, repo_path: str = ".", github_token: str = "", github_username: str = "", github_repo: str = ""):
        """
        Initialize the Git manager.
        
        Args:
            repo_path: Path to the Git repository (defaults to current directory)
            github_token: GitHub token for API access
            github_username: GitHub username for API access
            github_repo: GitHub repository name for API access
        """
        self.repo_path = os.path.abspath(repo_path)
        self.github_token = github_token
        self.github_username = github_username
        self.github_repo = github_repo
            
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
        timestamp = "2025-01-07T15:45:21-05:00"
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
        Push a message file to the repository.
        
        Args:
            filepath: Path to the message file
            commit_message: Git commit message
            
        Returns:
            Git commit hash if successful, None otherwise
        """
        try:
            # Get relative path for git commands
            rel_path = os.path.relpath(filepath, self.repo_path)
            
            # Stage the file
            subprocess.run(["git", "add", rel_path], cwd=self.repo_path, check=True)
            
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
            print(f"Output: {e.output if hasattr(e, 'output') else 'No output'}")
            return None

    def get_messages(self) -> list:
        """
        Get all messages from the messages directory.
        
        Returns:
            List of message dictionaries
        """
        messages = []
        if os.path.exists(self.messages_dir):
            for filename in os.listdir(self.messages_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(self.messages_dir, filename), 'r') as f:
                        try:
                            message = json.load(f)
                            messages.append(message)
                        except json.JSONDecodeError:
                            print(f"Error reading message file: {filename}")
        return sorted(messages, key=lambda x: x.get('timestamp', ''))

    def get_commit_messages(self, page: int = 1, per_page: int = 30) -> dict:
        """
        Fetch commit messages from GitHub repository using the GitHub REST API.
        
        Args:
            page: Page number for pagination (default: 1)
            per_page: Number of commits per page (default: 30, max: 100)
            
        Returns:
            dict: {
                "commits": [
                    {
                        "sha": str,
                        "message": str,
                        "author": str,
                        "date": str,
                        "url": str
                    }
                ],
                "pagination": {
                    "total": int,
                    "page": int,
                    "per_page": int,
                    "has_next": bool
                }
            }
        
        Raises:
            GitHubError: If there's an error fetching commits
            ValueError: If GitHub token is not provided
        """
        if not self.github_token:
            raise ValueError("GitHub token is required to fetch commit messages")
            
        # GitHub API endpoint for commits
        api_url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/commits"
        
        # Request headers
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"GitMessenger-{self.github_username}"
        }
        
        # Query parameters
        params = {
            "page": page,
            "per_page": min(per_page, 100)  # GitHub API limit
        }
        
        try:
            # Make API request
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            
            # Get total commit count from API response headers
            total_commits = per_page  # Default to current page size
            if "Link" in response.headers:
                # Parse Link header to get total pages
                links = requests.utils.parse_header_links(response.headers["Link"])
                for link in links:
                    if link["rel"] == "last":
                        # Extract page number from last link
                        last_page = int(parse_qs(urlparse(link["url"]).query)["page"][0])
                        total_commits = last_page * per_page
            
            # Parse commit data
            commits_data = response.json()
            commits = []
            
            for commit in commits_data:
                commits.append({
                    "sha": commit["sha"],
                    "message": commit["commit"]["message"],
                    "author": commit["commit"]["author"]["name"],
                    "date": commit["commit"]["author"]["date"],
                    "url": commit["html_url"]
                })
            
            # Check if there's a next page
            has_next = False
            if "Link" in response.headers:
                links = requests.utils.parse_header_links(response.headers["Link"])
                has_next = any(link["rel"] == "next" for link in links)
            
            return {
                "commits": commits,
                "pagination": {
                    "total": total_commits,
                    "page": page,
                    "per_page": per_page,
                    "has_next": has_next
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise GitHubError(f"Failed to fetch commit messages: {str(e)}")

    def get_commit_by_sha(self, commit_sha: str) -> dict:
        """
        Fetch a specific commit by its SHA.
        
        Args:
            commit_sha: The SHA of the commit to fetch
            
        Returns:
            dict: Commit details including message, author, and changes
            
        Raises:
            GitHubError: If there's an error fetching the commit
            ValueError: If GitHub token is not provided
        """
        if not self.github_token:
            raise ValueError("GitHub token is required to fetch commit details")
            
        api_url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/commits/{commit_sha}"
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"GitMessenger-{self.github_username}"
        }
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            commit_data = response.json()
            return {
                "sha": commit_data["sha"],
                "message": commit_data["commit"]["message"],
                "author": commit_data["commit"]["author"]["name"],
                "date": commit_data["commit"]["author"]["date"],
                "url": commit_data["html_url"],
                "stats": {
                    "additions": commit_data["stats"]["additions"],
                    "deletions": commit_data["stats"]["deletions"],
                    "total": commit_data["stats"]["total"]
                },
                "files": [
                    {
                        "filename": file["filename"],
                        "status": file["status"],
                        "additions": file["additions"],
                        "deletions": file["deletions"],
                        "changes": file["changes"]
                    }
                    for file in commit_data["files"]
                ]
            }
            
        except requests.exceptions.RequestException as e:
            raise GitHubError(f"Failed to fetch commit details: {str(e)}")

class GitHubError(Exception):
    """Custom exception for GitHub API errors."""
    pass

def main():
    """Example usage of GitManager."""
    # Initialize GitManager with current directory
    git_manager = GitManager(github_token="your_token", github_username="your_username", github_repo="your_repo")
    
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
        
        # Show all messages
        messages = git_manager.get_messages()
        print("\nAll messages:")
        for msg in messages:
            print(f"{msg['timestamp']} - {msg['author']}: {msg['content']}")
        
        # Fetch commit messages
        commit_messages = git_manager.get_commit_messages()
        print("\nCommit messages:")
        for commit in commit_messages["commits"]:
            print(f"{commit['sha']}: {commit['message']} by {commit['author']} on {commit['date']}")
            
    else:
        print("Failed to push message")

if __name__ == "__main__":
    main()
