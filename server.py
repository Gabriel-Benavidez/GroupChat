#!/usr/bin/env python3

import http.server
import socketserver
import json
import urllib.parse
import os
import sqlite3
from http import HTTPStatus
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime, timezone
import time
import threading
from github_manager import GitHubManager

class DatabaseManager:
    """Manages SQLite database operations for multiple repositories."""
    
    def __init__(self, db_path: str = "database/messages.db"):
        """Initialize database connection."""
        self.db_path = db_path
        print(f"Initializing DatabaseManager with path: {db_path}")
        self._init_database()
        self.github = GitHubManager()
        self._start_sync_thread()
        
    def _init_database(self) -> None:
        """Initialize the database with the schema."""
        try:
            with self.get_connection() as conn:
                # Read and execute schema
                schema_path = Path("database/schema_v2.sql")
                with open(schema_path) as f:
                    conn.executescript(f.read())
                conn.commit()
                
                # Test connection and print info
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"Found tables in database: {tables}")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise
    
    def _start_sync_thread(self) -> None:
        """Start background thread for repository synchronization."""
        self.sync_thread = threading.Thread(target=self._sync_repositories_periodically, daemon=True)
        self.sync_thread.start()
    
    def _sync_repositories_periodically(self) -> None:
        """Periodically sync all active repositories."""
        while True:
            try:
                repositories = self.get_repositories(active_only=True)
                for repo in repositories:
                    try:
                        self.sync_repository(repo['id'])
                    except Exception as e:
                        print(f"Error syncing repository {repo['url']}: {str(e)}")
            except Exception as e:
                print(f"Error in sync thread: {str(e)}")
            
            # Sleep for 5 minutes before next sync
            time.sleep(300)
    
    def sync_repository(self, repo_id: int) -> None:
        """
        Sync messages from a GitHub repository.
        
        Args:
            repo_id: Repository ID to sync
        """
        with self.get_connection() as conn:
            # Get repository info
            cursor = conn.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,))
            repo = cursor.fetchone()
            if not repo:
                raise ValueError(f"Repository {repo_id} not found")
            
            # Get last sync time
            last_synced = repo['last_synced']
            
            try:
                # Fetch messages from GitHub
                messages = self.github.get_all_repository_messages(repo['url'], since=last_synced)
                
                # Save new messages
                for msg in messages:
                    cursor.execute("""
                        INSERT INTO messages 
                        (repository_id, content, timestamp, author, url, message_type, parent_title)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        repo_id,
                        msg['content'],
                        msg['timestamp'],
                        msg['author'],
                        msg['url'],
                        msg['type'],
                        msg.get('parent_title')
                    ))
                
                # Update last sync time
                cursor.execute("""
                    UPDATE repositories 
                    SET last_synced = ? 
                    WHERE id = ?
                """, (datetime.now(timezone.utc).isoformat(), repo_id))
                
                conn.commit()
                print(f"Successfully synced {len(messages)} messages from {repo['url']}")
                
            except Exception as e:
                print(f"Error syncing repository {repo['url']}: {str(e)}")
                raise

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for named columns
        return conn

    def add_repository(self, name: str, url: str) -> int:
        """
        Add a new repository to track.
        
        Returns:
            Repository ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO repositories (name, url)
                VALUES (?, ?)
            """, (name, url))
            
            if cursor.rowcount == 0:  # Repository already exists
                cursor.execute("SELECT id FROM repositories WHERE url = ?", (url,))
                return cursor.fetchone()['id']
            
            repo_id = cursor.lastrowid
            
            # Start initial sync in background
            threading.Thread(
                target=self.sync_repository,
                args=(repo_id,),
                daemon=True
            ).start()
            
            return repo_id

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
        if self.path == '/messages':
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
                
                # Save to database
                repository_id = self.db_manager.add_repository(
                    name=message_data.get('repository_name', 'Default Repository'),
                    url=message_data.get('repository_url', 'local')
                )
                
                message_id = self.db_manager.save_message(
                    repository_id=repository_id,
                    content=content,
                    timestamp=timestamp,
                    author=author
                )
                
                self.send_json_response({
                    "message": "Message saved successfully",
                    "id": message_id
                })
                
            except json.JSONDecodeError:
                self.send_json_response(
                    {"error": "Invalid JSON"}, 
                    HTTPStatus.BAD_REQUEST
                )
            except Exception as e:
                print(f"Error saving message: {str(e)}")
                self.send_json_response(
                    {"error": "Failed to save message"}, 
                    HTTPStatus.INTERNAL_SERVER_ERROR
                )
        
        elif self.path == '/repositories':
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
                repo_data = json.loads(body)
                
                # Validate required fields
                if 'name' not in repo_data or 'url' not in repo_data:
                    self.send_json_response(
                        {"error": "Repository name and URL are required"}, 
                        HTTPStatus.BAD_REQUEST
                    )
                    return
                
                # Add repository
                repo_id = self.db_manager.add_repository(
                    name=repo_data['name'],
                    url=repo_data['url']
                )
                
                self.send_json_response({
                    "message": "Repository added successfully",
                    "id": repo_id
                })
                
            except json.JSONDecodeError:
                self.send_json_response(
                    {"error": "Invalid JSON"}, 
                    HTTPStatus.BAD_REQUEST
                )
            except Exception as e:
                print(f"Error adding repository: {str(e)}")
                self.send_json_response(
                    {"error": "Failed to add repository"}, 
                    HTTPStatus.INTERNAL_SERVER_ERROR
                )
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

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
