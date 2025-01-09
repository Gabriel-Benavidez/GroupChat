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
                conn.commit()
                print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
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
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO messages 
                    (repository_id, content, timestamp, author, message_type)
                    VALUES (?, ?, ?, ?, 'local')
                """, (repository_id, content, timestamp, author))
                conn.commit()
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
                    sort_order: str = "DESC", repository_ids: Optional[List[int]] = None,
                    message_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Get messages from the database with filtering and pagination.
        
        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            sort_order: Sort order ("ASC" or "DESC")
            repository_ids: Optional list of repository IDs to filter by
            message_types: Optional list of message types to filter by
            
        Returns:
            List of message dictionaries
        """
        with self.get_connection() as conn:
            query = """
                SELECT m.*, r.name as repository_name, r.url as repository_url
                FROM messages m
                JOIN repositories r ON m.repository_id = r.id
                WHERE 1=1
            """
            
            params = []
            
            if repository_ids:
                query += " AND m.repository_id IN ({})".format(
                    ','.join('?' * len(repository_ids))
                )
                params.extend(repository_ids)
            
            if message_types:
                query += " AND m.message_type IN ({})".format(
                    ','.join('?' * len(message_types))
                )
                params.extend(message_types)
            
            query += f" ORDER BY m.timestamp {sort_order}"
            
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

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
                
        elif parsed_path.path == '/messages':
            print("Handling /messages request...")
            try:
                # Parse parameters
                limit = int(query_params.get('limit', [20])[0])
                offset = int(query_params.get('offset', [0])[0])
                sort_order = query_params.get('sort', ['DESC'])[0]
                
                # Parse repository IDs if provided
                repository_ids = None
                if 'repositories' in query_params:
                    try:
                        repository_ids = [
                            int(repo_id) 
                            for repo_id in query_params['repositories'][0].split(',')
                        ]
                    except ValueError:
                        self.send_json_response(
                            {"error": "Invalid repository IDs"}, 
                            HTTPStatus.BAD_REQUEST
                        )
                        return
                
                # Parse message types if provided
                message_types = None
                if 'types' in query_params:
                    message_types = query_params['types'][0].split(',')
                
                print(f"Fetching messages with limit={limit}, offset={offset}, "
                      f"sort={sort_order}, repositories={repository_ids}, types={message_types}")
                
                # Get messages with pagination and repository filtering
                messages = self.db_manager.get_messages(
                    limit=limit,
                    offset=offset,
                    sort_order=sort_order,
                    repository_ids=repository_ids,
                    message_types=message_types
                )
                
                # Get total message count
                total_messages = self.db_manager.get_message_count(repository_ids, message_types)
                
                # Prepare response with pagination metadata
                response = {
                    "messages": messages,
                    "pagination": {
                        "total": total_messages,
                        "offset": offset,
                        "limit": limit,
                        "has_more": (offset + limit) < total_messages
                    }
                }
                
                self.send_json_response(response)
                
            except Exception as e:
                print(f"Error getting messages: {str(e)}")
                self.send_json_response(
                    {"error": "Failed to get messages"}, 
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

    def do_POST(self) -> None:
        """Handle POST requests."""
        try:
            if self.path == '/push':
                try:
                    result = subprocess.run(['./push.py'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.send_json_response({
                            "status": "success",
                            "message": result.stdout.strip() or "Successfully pushed changes"
                        })
                    else:
                        self.send_json_response({
                            "status": "error",
                            "message": result.stderr.strip() or "Failed to push changes"
                        }, HTTPStatus.INTERNAL_SERVER_ERROR)
                except Exception as e:
                    self.send_json_response({
                        "status": "error",
                        "message": str(e)
                    }, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            
            elif self.path == '/messages':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_json_response(
                        {"error": "Empty request body"}, 
                        HTTPStatus.BAD_REQUEST
                    )
                    return

                try:
                    # Parse request body
                    body = self.rfile.read(content_length)
                    print(f"Received message body: {body.decode()}")
                    message_data = json.loads(body)
                    
                    # Validate required fields
                    if 'content' not in message_data:
                        self.send_json_response(
                            {"error": "Message content is required"}, 
                            HTTPStatus.BAD_REQUEST
                        )
                        return
                    
                    # Get message details
                    content = message_data['content']
                    timestamp = message_data.get('timestamp', datetime.utcnow().isoformat())
                    author = message_data.get('author', 'Anonymous')
                    
                    print(f"Processing message: content={content}, timestamp={timestamp}, author={author}")
                    
                    # Save to database
                    repository_id = self.db_manager.add_repository(
                        name=message_data.get('repository_name', 'Default Repository'),
                        url=message_data.get('repository_url', 'local')
                    )
                    
                    print(f"Created/found repository with ID: {repository_id}")
                    
                    message_id = self.db_manager.save_message(
                        repository_id=repository_id,
                        content=content,
                        timestamp=timestamp,
                        author=author
                    )
                    
                    print(f"Saved message with ID: {message_id}")
                    
                    self.send_json_response({
                        "message": "Message saved successfully",
                        "id": message_id
                    })
                    
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}")
                    self.send_json_response(
                        {"error": "Invalid JSON"}, 
                        HTTPStatus.BAD_REQUEST
                    )
                except Exception as e:
                    print(f"Error saving message: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    self.send_json_response(
                        {"error": "Failed to save message"}, 
                        HTTPStatus.INTERNAL_SERVER_ERROR
                    )
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

def run_server(port: int = 8888) -> None:
    """
    Run the HTTP server on the specified port.
    
    Args:
        port: Port number to listen on
    """
    retries = 3
    while retries > 0:
        try:
            print(f"Starting server on port {port}...")
            server = socketserver.TCPServer(("", port), MessageHandler)
            server.allow_reuse_address = True
            server.serve_forever()
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"Port {port} is in use, trying again in 2 seconds...")
                time.sleep(2)
                retries -= 1
                if retries == 0:
                    port += 1
                    retries = 3
                    print(f"Trying port {port}...")
            else:
                raise
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.shutdown()
            server.server_close()
            break

if __name__ == "__main__":
    run_server()
