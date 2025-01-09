Please create a Git-based message storage system with the following requirements:

1. Create a Python web server that:
   - Runs on port 8888
   - Stores messages in both Git (as JSON files) and SQLite
   - Integrates with GitHub for remote operations
   - Uses Python 3.9+
   - Implements custom HTTP request handler for message operations

2. Set up the following database tables:
   - repositories: Track Git repositories with fields for id, name, url, last_synced, is_active, and created_at
   - messages: Store message data with fields for id, repository_id, content, timestamp, author, url, message_type, and parent_title

3. Implement message storage that:
   - Creates timestamped JSON files in a messages directory
   - Stores message content, author, and timestamp in each file
   - Updates the SQLite database for efficient querying
   - Uses ISO format for all timestamps
   - Implements pagination for message retrieval
   - Supports filtering by repository IDs and message types
   - Maintains proper message ordering with sort options

4. Create these core files:
   - server.py: Main HTTP server with GET/POST handlers
   - git_manager.py: Git operations handler
   - init_db.py: Database initialization
   - requirements.txt: Python dependencies
   - .env.template: Environment variable template
   - templates/index.html: Main web interface

5. Include these features:
   - GitHub API integration using a personal access token
   - Static file serving
   - JSON-based API responses
   - Error handling with proper HTTP status codes
   - Type hints throughout the codebase
   - Support for Git operations (add, commit, push)
   - Commit message handling and retrieval
   - Repository synchronization status tracking

6. API Endpoints:
   - GET /:  Serve main page
   - GET /repositories: List all repositories
   - GET /messages: Retrieve messages with pagination and filtering
   - POST /push: Push changes to GitHub

7. Security requirements:
   - Store GitHub token in environment variables
   - Validate all API inputs
   - Handle GitHub API errors gracefully
   - Secure file operations
   - Proper error handling for Git operations
   - Safe subprocess execution for Git commands

The system should be well-organized, maintainable, and include proper error handling throughout. Please implement this step by step, starting with the basic project structure and building up the functionality.
