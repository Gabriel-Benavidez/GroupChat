import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timezone
import time
from dotenv import load_dotenv

load_dotenv()

class GitHubManager:
    """Manages interactions with GitHub repositories."""
    
    def __init__(self):
        """Initialize GitHub manager with API token."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        
    def get_repository_issues(self, repo_url: str, since: Optional[str] = None) -> List[Dict]:
        """
        Get issues and comments from a GitHub repository.
        
        Args:
            repo_url: Full GitHub repository URL
            since: ISO 8601 timestamp to filter issues updated after this time
            
        Returns:
            List of issues with their comments
        """
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2:]
        
        # Build API URL for issues
        api_url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        params = {
            'state': 'all',
            'sort': 'updated',
            'direction': 'desc',
            'per_page': 100
        }
        if since:
            params['since'] = since
            
        messages = []
        try:
            # Get issues
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            issues = response.json()
            
            for issue in issues:
                # Add issue as a message
                messages.append({
                    'content': issue['body'],
                    'timestamp': issue['created_at'],
                    'author': issue['user']['login'],
                    'url': issue['html_url'],
                    'type': 'issue',
                    'title': issue['title']
                })
                
                # Get comments for this issue
                comments_url = issue['comments_url']
                response = self.session.get(comments_url)
                response.raise_for_status()
                comments = response.json()
                
                for comment in comments:
                    messages.append({
                        'content': comment['body'],
                        'timestamp': comment['created_at'],
                        'author': comment['user']['login'],
                        'url': comment['html_url'],
                        'type': 'comment',
                        'parent_title': issue['title']
                    })
                    
                # Rate limit handling
                self._handle_rate_limit(response)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issues from {repo_url}: {str(e)}")
            raise
            
        return messages
    
    def get_repository_discussions(self, repo_url: str) -> List[Dict]:
        """
        Get discussions and their comments from a GitHub repository.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            List of discussions with their comments
        """
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2:]
        
        # GraphQL query for discussions
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                title
                body
                createdAt
                url
                author {
                  login
                }
                comments(first: 50) {
                  nodes {
                    body
                    createdAt
                    author {
                      login
                    }
                    url
                  }
                }
              }
            }
          }
        }
        """
        
        messages = []
        try:
            # Make GraphQL request
            response = self.session.post(
                'https://api.github.com/graphql',
                json={'query': query, 'variables': {'owner': owner, 'repo': repo}}
            )
            response.raise_for_status()
            data = response.json()
            
            # Process discussions
            discussions = data['data']['repository']['discussions']['nodes']
            for discussion in discussions:
                # Add discussion as a message
                messages.append({
                    'content': discussion['body'],
                    'timestamp': discussion['createdAt'],
                    'author': discussion['author']['login'],
                    'url': discussion['url'],
                    'type': 'discussion',
                    'title': discussion['title']
                })
                
                # Add discussion comments
                for comment in discussion['comments']['nodes']:
                    messages.append({
                        'content': comment['body'],
                        'timestamp': comment['createdAt'],
                        'author': comment['author']['login'],
                        'url': comment['url'],
                        'type': 'discussion_comment',
                        'parent_title': discussion['title']
                    })
                    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching discussions from {repo_url}: {str(e)}")
            raise
            
        return messages
    
    def get_all_repository_messages(self, repo_url: str, since: Optional[str] = None) -> List[Dict]:
        """
        Get all messages (issues, comments, discussions) from a repository.
        
        Args:
            repo_url: Full GitHub repository URL
            since: ISO 8601 timestamp to filter content updated after this time
            
        Returns:
            List of all messages from the repository
        """
        messages = []
        
        # Get issues and their comments
        try:
            messages.extend(self.get_repository_issues(repo_url, since))
        except Exception as e:
            print(f"Warning: Failed to fetch issues: {str(e)}")
        
        # Get discussions and their comments
        try:
            messages.extend(self.get_repository_discussions(repo_url))
        except Exception as e:
            print(f"Warning: Failed to fetch discussions: {str(e)}")
        
        # Sort all messages by timestamp
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return messages
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle GitHub API rate limiting."""
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining < 10:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = reset_time - time.time()
            if sleep_time > 0:
                print(f"Rate limit low. Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)
