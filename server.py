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
    def __init__(self, messages_dir: str = "messages"):
        self.messages_dir = messages_dir
        os.makedirs(messages_dir, exist_ok=True)
    
    def save_message(self, content: str, author: str) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        filename = f"{timestamp.replace(':', '-')}_{author}.txt"
        filepath = os.path.join(self.messages_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"Author: {author}\nTimestamp: {timestamp}\n\n{content}")
        
        return filepath
    
    def get_messages(self) -> List[Dict[str, Any]]:
        messages = []
        for filename in sorted(os.listdir(self.messages_dir)):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.messages_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                    # Parse the content
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
        try:
            if self.path == '/send_message':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                message = data.get('message', '')
                author = data.get('author', 'Anonymous')
                
                filepath = self.message_manager.save_message(message, author)
                
                self.send_json_response({
                    'status': 'success',
                    'message': 'Message saved successfully',
                    'filepath': filepath
                })
            elif self.path == '/get_messages':
                messages = self.message_manager.get_messages()
                self.send_json_response({
                    'messages': messages
                })
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
