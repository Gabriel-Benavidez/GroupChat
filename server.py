#!/usr/bin/env python3

import http.server
import socketserver
import json
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

class MessageManager:
    def __init__(self, messages_dir: str = "message_storage"):
        """Initialize the message manager with a dedicated storage directory."""
        self.messages_dir = messages_dir
        os.makedirs(messages_dir, exist_ok=True)
        print(f"Message storage initialized at: {os.path.abspath(messages_dir)}")
    
    def save_message(self, content: str, author: str) -> str:
        """Save a message to a text file."""
        timestamp = datetime.now(timezone.utc).isoformat()
        filename = f"{timestamp.replace(':', '-')}_{author}.txt"
        filepath = os.path.join(self.messages_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                f.write(f"Author: {author}\nTimestamp: {timestamp}\n\n{content}")
            print(f"Message saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            raise
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from the storage directory."""
        messages = []
        if os.path.exists(self.messages_dir):
            for filename in sorted(os.listdir(self.messages_dir)):
                if filename.endswith('.txt') and filename != '.gitkeep':
                    filepath = os.path.join(self.messages_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            lines = content.split('\n')
                            author = lines[0].replace('Author: ', '')
                            timestamp = lines[1].replace('Timestamp: ', '')
                            message_content = '\n'.join(lines[3:])
                            messages.append({
                                'author': author,
                                'timestamp': timestamp,
                                'content': message_content,
                                'filename': filename
                            })
                    except Exception as e:
                        print(f"Error reading message {filename}: {str(e)}")
        return messages

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the messaging application."""
    
    def __init__(self, *args, **kwargs):
        # Initialize message manager
        self.message_manager = MessageManager()
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        if parsed_path.path == '/':
            # Serve the main page
            print("Serving main page...")
            self.serve_file('templates/index.html', 'text/html')
            
        elif parsed_path.path == '/messages':
            print("Handling /messages request...")
            try:
                messages = self.message_manager.get_messages()
                self.send_json_response({"messages": messages})
            except Exception as e:
                print(f"Error getting messages: {str(e)}")
                self.send_json_response(
                    {"error": "Failed to get messages"}, 
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
        content_length = int(self.headers.get('Content-Length', 0))
        
        try:
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/send_message':
                message = data.get('message', '').strip()
                author = data.get('author', 'Anonymous').strip()
                
                if not message:
                    self.send_json_response({
                        'status': 'error',
                        'message': 'Message content is required'
                    }, HTTPStatus.BAD_REQUEST)
                    return
                
                try:
                    filepath = self.message_manager.save_message(message, author)
                    self.send_json_response({
                        'status': 'success',
                        'message': 'Message saved successfully',
                        'filepath': filepath
                    })
                except Exception as e:
                    self.send_json_response({
                        'status': 'error',
                        'message': f'Failed to save message: {str(e)}'
                    }, HTTPStatus.INTERNAL_SERVER_ERROR)
            
            elif self.path == '/push_to_github':
                try:
                    # Add all files in message_storage
                    subprocess.run(['git', 'add', 'message_storage/*.txt'], 
                                cwd=os.path.dirname(os.path.abspath(__file__)),
                                check=True)
                    
                    # Check if there are changes to commit
                    result = subprocess.run(['git', 'status', '--porcelain'],
                                         cwd=os.path.dirname(os.path.abspath(__file__)),
                                         capture_output=True,
                                         text=True,
                                         check=True)
                    
                    if result.stdout.strip():
                        # Commit the changes
                        commit_message = f"Add new messages - {datetime.now(timezone.utc).isoformat()}"
                        subprocess.run(['git', 'commit', '-m', commit_message],
                                    cwd=os.path.dirname(os.path.abspath(__file__)),
                                    check=True)
                        
                        # Push to GitHub
                        subprocess.run(['git', 'push', 'origin', 'main'],
                                    cwd=os.path.dirname(os.path.abspath(__file__)),
                                    check=True)
                        
                        self.send_json_response({
                            'status': 'success',
                            'message': 'Messages successfully pushed to GitHub'
                        })
                    else:
                        self.send_json_response({
                            'status': 'success',
                            'message': 'No new messages to push'
                        })
                except subprocess.CalledProcessError as e:
                    self.send_json_response({
                        'status': 'error',
                        'message': f'Failed to push to GitHub: {str(e)}'
                    }, HTTPStatus.INTERNAL_SERVER_ERROR)
            
            elif self.path == '/get_messages':
                try:
                    messages = self.message_manager.get_messages()
                    self.send_json_response({'messages': messages})
                except Exception as e:
                    self.send_json_response({
                        'status': 'error',
                        'message': f'Failed to get messages: {str(e)}'
                    }, HTTPStatus.INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            self.send_json_response({
                'status': 'error',
                'message': f'Server error: {str(e)}'
            }, HTTPStatus.INTERNAL_SERVER_ERROR)
    
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
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

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
