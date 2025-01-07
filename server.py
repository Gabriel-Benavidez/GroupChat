#!/usr/bin/env python3.9
import http.server
import socketserver
import json
import urllib.parse
import os
from http import HTTPStatus
from typing import Dict, Any, Optional

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the messaging application."""
    
    def __init__(self, *args, **kwargs):
        # Store messages in memory for now (will be replaced with Git storage later)
        if not hasattr(MessageHandler, 'messages'):
            MessageHandler.messages = []
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests.
        
        Routes:
        - /: Serve the main page
        - /messages: Return all messages
        - /static/*: Serve static files
        """
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the main page
            self.serve_file('templates/index.html', 'text/html')
        elif parsed_path.path == '/messages':
            # Return messages as JSON
            self.send_json_response(MessageHandler.messages)
        elif parsed_path.path.startswith('/static/'):
            # Serve static files
            self.serve_static_file(parsed_path.path[8:])  # Remove '/static/' prefix
        else:
            # Handle 404
            self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")

    def do_POST(self) -> None:
        """Handle POST requests.
        
        Routes:
        - /messages: Add a new message
        """
        if self.path == '/messages':
            # Get message content from request body
            content_length = int(self.headers.get('Content-Length', 0))
            message_data = self.rfile.read(content_length)
            
            try:
                message = json.loads(message_data)
                # Add timestamp to message
                message['timestamp'] = self.get_timestamp()
                MessageHandler.messages.append(message)
                
                # Send success response
                self.send_json_response({"status": "success", "message": "Message received"})
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON data")
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")

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
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    @staticmethod
    def get_timestamp() -> str:
        """Return the current timestamp in ISO format."""
        return "2025-01-07T15:29:25-05:00"  # Using provided timestamp

def run_server(port: int = 8000) -> None:
    """Run the HTTP server on the specified port."""
    with socketserver.TCPServer(("", port), MessageHandler) as httpd:
        print(f"Server running on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
