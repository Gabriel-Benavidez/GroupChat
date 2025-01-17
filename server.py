#!/usr/bin/env python3

import http.server
import socketserver
import json
import sqlite3
import os
import time
import threading
import urllib.parse
import subprocess
import traceback
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from github_manager import GitHubManager

class DatabaseManager:
    def __init__(self, db_path: str = "database/messages.db"):
        self.db_path = db_path
        print(f"Initializing DatabaseManager with path: {db_path}")
        self._init_database()
        self.github = GitHubManager()
        
    def _init_database(self) -> None:
        """Initialize the database with the schema."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with self.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        last_synced TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(url)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repository_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        author TEXT,
                        url TEXT,
                        message_type TEXT,
                        parent_title TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (repository_id) REFERENCES repositories(id)
                    )
                """)
                
                # Add default repository if it doesn't exist
                conn.execute("""
                    INSERT OR IGNORE INTO repositories (id, name, url) 
                    VALUES (1, 'default', 'default')
                """)
                conn.commit()
                print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

    def get_connection(self):
        """Get a database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def add_repository(self, name: str, url: str) -> int:
        """Add a new repository to track."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO repositories (name, url) VALUES (?, ?)",
                    (name, url)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    cursor = conn.execute(
                        "SELECT id FROM repositories WHERE url = ?",
                        (url,)
                    )
                    row = cursor.fetchone()
                    return row['id']
                return cursor.lastrowid
        except Exception as e:
            print(f"Error in add_repository: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def save_message(self, repository_id: int, content: str, timestamp: str, author: str) -> int:
        """Save a new message to the database."""
        try:
            print(f"Attempting to save message: repo_id={repository_id}, content={content}, author={author}")
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO messages 
                    (repository_id, content, timestamp, author, message_type)
                    VALUES (?, ?, ?, ?, 'local')
                """, (repository_id, content, timestamp, author))
                conn.commit()
                print(f"Successfully saved message with ID: {cursor.lastrowid}")
                return cursor.lastrowid
        except Exception as e:
            print(f"Error in save_message: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def get_repositories(self, active_only: bool = True) -> List[Dict]:
        """Get list of tracked repositories."""
        with self.get_connection() as conn:
            query = "SELECT * FROM repositories"
            if active_only:
                query += " WHERE is_active = TRUE"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        
    def get_messages(self, limit: Optional[int] = None, offset: int = 0,
                    sort_order: str = "DESC") -> List[Dict[str, Any]]:
        """Get messages from the database."""
        try:
            print("Attempting to get messages from database...")
            with self.get_connection() as conn:
                query = """
                    SELECT m.*, r.name as repository_name 
                    FROM messages m
                    JOIN repositories r ON m.repository_id = r.id
                    ORDER BY m.timestamp {}
                """.format(sort_order)
                
                if limit is not None:
                    query += f" LIMIT {limit}"
                if offset:
                    query += f" OFFSET {offset}"
                
                print(f"Executing query: {query}")
                cursor = conn.execute(query)
                messages = []
                for row in cursor:
                    messages.append({
                        'id': row['id'],
                        'content': row['content'],
                        'timestamp': row['timestamp'],
                        'author': row['author'],
                        'repository': row['repository_name']
                    })
                print(f"Found {len(messages)} messages")
                return messages
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            raise

    def get_message_count(self, repository_ids: Optional[List[int]] = None,
                         message_types: Optional[List[str]] = None) -> int:
        """Get total number of messages with optional filtering."""
        with self.get_connection() as conn:
            query = "SELECT COUNT(*) as count FROM messages WHERE 1=1"
            params = []
            
            if repository_ids:
                query += " AND repository_id IN ({})".format(
                    ','.join('?' * len(repository_ids))
                )
                params.extend(repository_ids)
            
            if message_types:
                query += " AND message_type IN ({})".format(
                    ','.join('?' * len(message_types))
                )
                params.extend(message_types)
            
            cursor = conn.execute(query, params)
            return cursor.fetchone()['count']

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the messaging application."""
    
    def __init__(self, *args, **kwargs):
        # Initialize database and git managers
        self.db_manager = DatabaseManager()
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        try:
            if self.path.startswith('/messages'):
                messages = self.db_manager.get_messages(limit=50)
                self.send_json_response(messages)
                return
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if parsed_path.path == '/':
                # Serve the main page
                print("Serving main page...")
                self.serve_file('templates/index.html', 'text/html')
                
            elif parsed_path.path == '/repositories':
                print("Handling /repositories request...")
                try:
                    repositories = self.db_manager.get_repositories()
                    self.send_json_response({"repositories": repositories})
                except Exception as e:
                    print(f"Error getting repositories: {str(e)}")
                    self.send_json_response(
                        {"error": "Failed to get repositories"}, 
                        HTTPStatus.INTERNAL_SERVER_ERROR
                    )
                    
            elif parsed_path.path == '/push':
                print("Handling /push request...")
                try:
                    # Parse request body
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length == 0:
                        self.send_json_response(
                            {"error": "Empty request body"}, 
                            HTTPStatus.BAD_REQUEST
                        )
                        return

                    body = self.rfile.read(content_length)
                    # Push to GitHub
                    success, error = self.db_manager.github.push()
                    if success:
                        self.send_json_response({"status": "success", "message": "Successfully pushed to GitHub"})
                    else:
                        self.send_json_response({"status": "error", "message": f"Failed to push: {error}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
                    
                except Exception as e:
                    print(f"Error pushing to GitHub: {str(e)}")
                    self.send_json_response(
                        {"error": "Failed to push to GitHub"}, 
                        HTTPStatus.INTERNAL_SERVER_ERROR
                    )
            else:
                # Try to serve static files
                try:
                    self.serve_static_file(parsed_path.path.lstrip('/'))
                except FileNotFoundError:
                    self.send_error(HTTPStatus.NOT_FOUND, "File not found")

        except Exception as e:
            print(f"Error in do_GET: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.send_json_response(
                {"error": "Internal server error"}, 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def do_POST(self) -> None:
        """Handle POST requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            print(f"Received POST data: {post_data.decode('utf-8')}")
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/messages':
                try:
                    # Validate required fields
                    if 'content' not in data:
                        self.send_json_response(
                            {"error": "Message content is required"}, 
                            HTTPStatus.BAD_REQUEST
                        )
                        return
                    
                    content = data['content'].strip()
                    if not content:
                        self.send_json_response(
                            {"error": "Message content cannot be empty"}, 
                            HTTPStatus.BAD_REQUEST
                        )
                        return
                    
                    # Get message details
                    timestamp = datetime.now(timezone.utc).isoformat()
                    author = data.get('author', 'Anonymous')
                    
                    print(f"Processing message: content={content}, timestamp={timestamp}, author={author}")
                    
                    # Save to database with default repository (id=1)
                    message_id = self.db_manager.save_message(
                        repository_id=1,
                        content=content,
                        timestamp=timestamp,
                        author=author
                    )
                    
                    print(f"Successfully saved message with ID: {message_id}")
                    
                    # Send success response with the message ID
                    self.send_json_response({
                        "status": "success",
                        "message": "Message saved successfully",
                        "id": message_id
                    })
                    
                except Exception as e:
                    print(f"Error saving message: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    self.send_json_response(
                        {"error": f"Failed to save message: {str(e)}"}, 
                        HTTPStatus.INTERNAL_SERVER_ERROR
                    )
                return
            
            elif self.path == '/push':
                try:
                    print("Attempting to push to GitHub...")
                    result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True, cwd=os.getcwd())
                    if result.returncode != 0:
                        raise Exception(f"Git add failed: {result.stderr}")
                    
                    result = subprocess.run(['git', 'commit', '-m', 'Update messages'], capture_output=True, text=True, cwd=os.getcwd())
                    if result.returncode != 0 and "nothing to commit" not in result.stderr:
                        raise Exception(f"Git commit failed: {result.stderr}")
                    
                    result = subprocess.run(['git', 'push'], capture_output=True, text=True, cwd=os.getcwd())
                    if result.returncode != 0:
                        raise Exception(f"Git push failed: {result.stderr}")
                    
                    print("Successfully pushed to GitHub")
                    self.send_json_response({
                        "status": "success",
                        "message": "Successfully pushed to GitHub"
                    })
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error pushing to GitHub: {error_msg}")
                    self.send_json_response({
                        "status": "error",
                        "message": f"Failed to push: {error_msg}"
                    }, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
        except Exception as e:
            print(f"Unhandled error in do_POST: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.send_json_response(
                {"error": "Internal server error"}, 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def serve_file(self, filepath: str, content_type: str) -> None:
        """Serve a file with the specified content type."""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def serve_static_file(self, filepath: str) -> None:
        """Serve static files with appropriate content types."""
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        
        _, ext = os.path.splitext(filepath)
        content_type = content_types.get(ext, 'application/octet-stream')
        self.serve_file(os.path.join('static', filepath), content_type)

    def send_json_response(self, data: Dict[str, Any], status: int = HTTPStatus.OK) -> None:
        """Send a JSON response with the specified data and status code."""
        try:
            response = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response))
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            print(f"Error in send_json_response: {str(e)}")
            print(f"Data being sent: {data}")
            import traceback
            traceback.print_exc()
            raise

def run_server(port: int = 8080) -> None:
    """
    Run the HTTP server on the specified port.
    
    Args:
        port: Port number to listen on
    """
    server = None
    try:
        print(f"Starting server on port {port}...")
        server = socketserver.TCPServer(("", port), MessageHandler)
        server.allow_reuse_address = True
        print(f"Server is running at http://localhost:{port}")
        server.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Error: Port {port} is already in use. Please try a different port or restart the server.")
        else:
            print(f"Error starting server: {e}")
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if server:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass

if __name__ == "__main__":
    run_server(8081)
