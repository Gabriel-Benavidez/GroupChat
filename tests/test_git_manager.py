#!/usr/bin/env python3

import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
from git_manager import GitManager

class TestGitManager(unittest.TestCase):
    """Test cases for GitManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_USERNAME': 'test_user',
            'GITHUB_REPO': 'test_repo'
        })
        self.env_patcher.start()
        
        # Initialize GitManager with test directory
        self.git_manager = GitManager(repo_path=self.test_dir)

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
        # Stop environment variables patch
        self.env_patcher.stop()

    def test_init(self):
        """Test GitManager initialization."""
        self.assertEqual(self.git_manager.repo_path, self.test_dir)
        self.assertEqual(self.git_manager.github_token, 'test_token')
        self.assertEqual(self.git_manager.github_username, 'test_user')
        self.assertEqual(self.git_manager.github_repo, 'test_repo')
        
        # Check if messages directory was created
        messages_dir = Path(self.test_dir) / "messages"
        self.assertTrue(messages_dir.exists())
        self.assertTrue(messages_dir.is_dir())

    def test_create_message_file(self):
        """Test message file creation."""
        content = "Test message"
        author = "test_author"
        
        # Create message file
        filepath = self.git_manager.create_message_file(content, author)
        
        # Check if file exists
        self.assertTrue(os.path.exists(filepath))
        
        # Verify file content
        with open(filepath, 'r') as f:
            message_data = json.load(f)
            self.assertEqual(message_data['content'], content)
            self.assertEqual(message_data['author'], author)
            self.assertTrue('timestamp' in message_data)

    @patch('subprocess.run')
    def test_push_message_success(self, mock_run):
        """Test successful message push to GitHub."""
        # Mock successful git commands
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            MagicMock(returncode=0, stdout="test_hash\n"),  # git rev-parse
            MagicMock(returncode=0)  # git push
        ]
        
        filepath = "test_message.json"
        commit_message = "Test commit"
        
        result = self.git_manager.push_message(filepath, commit_message)
        
        # Verify result
        self.assertEqual(result, "test_hash")
        
        # Verify git commands were called
        self.assertEqual(mock_run.call_count, 4)

    @patch('subprocess.run')
    def test_push_message_failure(self, mock_run):
        """Test failed message push to GitHub."""
        # Mock failed git command
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", output="error message"
        )
        
        filepath = "test_message.json"
        commit_message = "Test commit"
        
        result = self.git_manager.push_message(filepath, commit_message)
        
        # Verify result
        self.assertIsNone(result)

    @patch('subprocess.run')
    def test_clone_repository_success(self, mock_run):
        """Test successful repository cloning."""
        # Mock successful git clone
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.git_manager.clone_repository()
        
        # Verify result
        self.assertTrue(result)
        
        # Verify git clone was called with correct arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "git")
        self.assertEqual(args[1], "clone")
        self.assertTrue("test_token" in args[2])
        self.assertTrue("test_user" in args[2])
        self.assertTrue("test_repo" in args[2])

    @patch('subprocess.run')
    def test_clone_repository_failure(self, mock_run):
        """Test failed repository cloning."""
        # Mock failed git clone
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", output="error message"
        )
        
        result = self.git_manager.clone_repository()
        
        # Verify result
        self.assertFalse(result)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
