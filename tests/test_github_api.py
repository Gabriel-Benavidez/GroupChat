#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import requests

# Add parent directory to path to import git_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from git_manager import GitManager, GitHubError

class TestGitHubAPI(unittest.TestCase):
    """Test cases for GitHub API integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.git_manager = GitManager(
            github_token="test_token",
            github_username="test_user",
            github_repo="test_repo"
        )

    def test_get_commit_messages_no_token(self):
        """Test getting commit messages without a token."""
        git_manager = GitManager()  # No token provided
        with self.assertRaises(ValueError):
            git_manager.get_commit_messages()

    @patch('requests.get')
    def test_get_commit_messages_success(self, mock_get):
        """Test successful retrieval of commit messages."""
        # Mock response data
        mock_commits = [
            {
                "sha": "abc123",
                "commit": {
                    "message": "Test commit",
                    "author": {
                        "name": "Test Author",
                        "date": "2025-01-07T16:12:37-05:00"
                    }
                },
                "html_url": "https://github.com/test/test/commit/abc123"
            }
        ]
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commits
        mock_response.headers = {
            "Link": '<https://api.github.com/repos/test/test/commits?page=2>; rel="next", '
                   '<https://api.github.com/repos/test/test/commits?page=3>; rel="last"'
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Get commit messages with per_page=30
        result = self.git_manager.get_commit_messages(per_page=30)

        # Verify request
        mock_get.assert_called_once()
        self.assertEqual(
            mock_get.call_args[1]["headers"]["Authorization"],
            "token test_token"
        )

        # Verify response
        self.assertEqual(len(result["commits"]), 1)
        self.assertEqual(result["commits"][0]["sha"], "abc123")
        self.assertEqual(result["commits"][0]["message"], "Test commit")
        self.assertTrue(result["pagination"]["has_next"])
        self.assertEqual(result["pagination"]["total"], 90)  # 3 pages * 30 per page

    @patch('requests.get')
    def test_get_commit_messages_error(self, mock_get):
        """Test error handling when getting commit messages."""
        # Mock error response
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        # Verify error handling
        with self.assertRaises(GitHubError) as context:
            self.git_manager.get_commit_messages()
        self.assertEqual(str(context.exception), "Failed to fetch commit messages: API Error")

    @patch('requests.get')
    def test_get_commit_by_sha_success(self, mock_get):
        """Test successful retrieval of a specific commit."""
        # Mock response data
        mock_commit = {
            "sha": "abc123",
            "commit": {
                "message": "Test commit",
                "author": {
                    "name": "Test Author",
                    "date": "2025-01-07T16:12:37-05:00"
                }
            },
            "html_url": "https://github.com/test/test/commit/abc123",
            "stats": {
                "additions": 10,
                "deletions": 5,
                "total": 15
            },
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 5,
                    "changes": 15
                }
            ]
        }

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Get commit details
        result = self.git_manager.get_commit_by_sha("abc123")

        # Verify request
        mock_get.assert_called_once()
        self.assertEqual(
            mock_get.call_args[1]["headers"]["Authorization"],
            "token test_token"
        )

        # Verify response
        self.assertEqual(result["sha"], "abc123")
        self.assertEqual(result["message"], "Test commit")
        self.assertEqual(result["stats"]["additions"], 10)
        self.assertEqual(result["stats"]["deletions"], 5)
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["filename"], "test.py")

    @patch('requests.get')
    def test_get_commit_by_sha_error(self, mock_get):
        """Test error handling when getting a specific commit."""
        # Mock error response
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        # Verify error handling
        with self.assertRaises(GitHubError) as context:
            self.git_manager.get_commit_by_sha("abc123")
        self.assertEqual(str(context.exception), "Failed to fetch commit details: API Error")

    def test_get_commit_by_sha_no_token(self):
        """Test getting a commit without a token."""
        git_manager = GitManager()  # No token provided
        with self.assertRaises(ValueError):
            git_manager.get_commit_by_sha("abc123")

if __name__ == '__main__':
    unittest.main()
