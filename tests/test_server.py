#!/usr/bin/env python3

import unittest
import json
import os
import sqlite3
import tempfile
import shutil
import threading
import http.server
import socketserver
import requests
import time
from pathlib import Path
from typing import Optional, Tuple, List
from unittest.mock import patch, MagicMock

# Import our server modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import MessageHandler, DatabaseManager, run_server
from git_manager import GitManager

class TestServer(unittest.TestCase):
    """Test cases for the messaging server."""
    
    server = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        """Set up the test server in a separate thread."""
        # Create a temporary directory for the test database and messages
        cls.test_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.test_dir, "test_messages.db")
        cls.messages_dir = os.path.join(cls.test_dir, "messages")
        os.makedirs(cls.messages_dir, exist_ok=True)

        # Initialize the test database
        cls.init_test_database()

        # Find an available port
        cls.server_port = cls.find_available_port()
        
        # Start the test server
        cls.server_thread = threading.Thread(
            target=cls.run_test_server,
            args=(cls.server_port, cls.db_path)
        )
        cls.server_thread.daemon = True
        cls.server_thread.start()

        # Wait for server to start
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop the server
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()
        
        # Remove temporary directory
        shutil.rmtree(cls.test_dir)

    @classmethod
    def find_available_port(cls) -> int:
        """Find an available port to use for testing."""
        with socketserver.TCPServer(("", 0), None) as s:
            return s.server_address[1]

    @classmethod
    def init_test_database(cls):
        """Initialize the test database with the schema."""
        with sqlite3.connect(cls.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    author TEXT,
                    git_commit_hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    @classmethod
    def run_test_server(cls, port: int, db_path: str):
        """Run the test server with the test database."""
        class TestMessageHandler(MessageHandler):
            def __init__(self, *args, **kwargs):
                self.db_manager = DatabaseManager(db_path=db_path)
                self.git_manager = GitManager(repo_path=os.path.dirname(db_path))
                super(http.server.SimpleHTTPRequestHandler, self).__init__(*args, **kwargs)

        cls.server = socketserver.TCPServer(("", port), TestMessageHandler)
        cls.server.serve_forever()

    def setUp(self):
        """Set up each test."""
        self.base_url = f"http://localhost:{self.server_port}"
        
        # Mock Git operations
        self.git_patcher = patch('git_manager.GitManager.push_message')
        self.mock_git_push = self.git_patcher.start()
        self.mock_git_push.return_value = "test_commit_hash"
        
        # Clear database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages")

    def tearDown(self):
        """Clean up after each test."""
        self.git_patcher.stop()

    def create_test_messages(self, count: int) -> List[dict]:
        """Create a specified number of test messages."""
        messages = []
        for i in range(count):
            message = {
                "content": f"Test message {i + 1}",
                "author": f"TestUser{i + 1}"
            }
            response = requests.post(
                f"{self.base_url}/messages",
                json=message
            )
            self.assertEqual(response.status_code, 200)
            messages.append(message)
        return messages

    def test_get_messages_empty(self):
        """Test getting messages when database is empty."""
        response = requests.get(f"{self.base_url}/messages")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("messages", data)
        self.assertIn("pagination", data)
        self.assertEqual(len(data["messages"]), 0)
        self.assertEqual(data["pagination"]["total"], 0)

    def test_get_messages_pagination(self):
        """Test message pagination."""
        # Create 25 test messages
        test_messages = self.create_test_messages(25)
        
        # Test first page
        response = requests.get(f"{self.base_url}/messages?limit=10&offset=0")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["messages"]), 10)
        self.assertEqual(data["pagination"]["total"], 25)
        self.assertTrue(data["pagination"]["has_more"])
        
        # Test second page
        response = requests.get(f"{self.base_url}/messages?limit=10&offset=10")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["messages"]), 10)
        self.assertEqual(data["pagination"]["offset"], 10)
        self.assertTrue(data["pagination"]["has_more"])
        
        # Test last page
        response = requests.get(f"{self.base_url}/messages?limit=10&offset=20")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["messages"]), 5)
        self.assertEqual(data["pagination"]["offset"], 20)
        self.assertFalse(data["pagination"]["has_more"])

    def test_get_messages_sorting(self):
        """Test message sorting."""
        # Create test messages
        test_messages = self.create_test_messages(3)
        
        # Test ascending order
        response = requests.get(f"{self.base_url}/messages?sort=ASC")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        messages = data["messages"]
        self.assertEqual(len(messages), 3)
        
        # Verify ascending order
        timestamps = [msg["timestamp"] for msg in messages]
        self.assertEqual(timestamps, sorted(timestamps))
        
        # Test descending order
        response = requests.get(f"{self.base_url}/messages?sort=DESC")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        messages = data["messages"]
        
        # Verify descending order
        timestamps = [msg["timestamp"] for msg in messages]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_get_messages_invalid_parameters(self):
        """Test invalid pagination parameters."""
        # Test invalid limit
        response = requests.get(f"{self.base_url}/messages?limit=invalid")
        self.assertEqual(response.status_code, 400)
        
        # Test invalid offset
        response = requests.get(f"{self.base_url}/messages?offset=invalid")
        self.assertEqual(response.status_code, 400)
        
        # Test invalid sort order
        response = requests.get(f"{self.base_url}/messages?sort=INVALID")
        self.assertEqual(response.status_code, 200)  # Should use default DESC
        data = response.json()
        self.assertIn("messages", data)

    def test_get_messages_default_parameters(self):
        """Test default pagination parameters."""
        # Create more than default limit messages
        test_messages = self.create_test_messages(25)
        
        # Test with no parameters
        response = requests.get(f"{self.base_url}/messages")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["messages"]), 20)  # Default limit
        self.assertEqual(data["pagination"]["offset"], 0)  # Default offset
        self.assertEqual(data["pagination"]["limit"], 20)  # Default limit
        self.assertTrue(data["pagination"]["has_more"])

    def test_get_messages(self):
        """Test retrieving messages."""
        # Create a test message
        message_data = {
            "content": "Test message for GET",
            "author": "TestUser"
        }
        response = requests.post(f"{self.base_url}/messages", json=message_data)
        self.assertEqual(response.status_code, 200)
        
        # Get messages
        response = requests.get(f"{self.base_url}/messages")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("messages", data)
        self.assertIn("pagination", data)
        
        messages = data["messages"]
        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), 1)
        
        message = messages[0]
        self.assertEqual(message["content"], message_data["content"])
        self.assertEqual(message["author"], message_data["author"])
        self.assertIn("timestamp", message)
        self.assertIn("git_commit_hash", message)

    def test_post_message(self):
        """Test posting a message and verifying storage."""
        message_data = {
            "content": "Test message",
            "author": "TestUser"
        }
        
        response = requests.post(f"{self.base_url}/messages", json=message_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("id", data)
        self.assertEqual(data["git_hash"], "test_commit_hash")
        
        # Verify database storage
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, author FROM messages WHERE id = ?", (data["id"],))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], message_data["content"])
            self.assertEqual(row[1], message_data["author"])

    def test_post_invalid_message(self):
        """Test posting an invalid message."""
        message_data = {
            "author": "TestUser"
            # Missing required content field
        }
        
        response = requests.post(f"{self.base_url}/messages", json=message_data)
        self.assertEqual(response.status_code, 400)

def main():
    unittest.main()

if __name__ == "__main__":
    main()
