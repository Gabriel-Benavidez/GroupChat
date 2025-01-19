# GroupChat

A simple real-time chat application with local message storage and optional GitHub backup.

## Quick Start Guide

1. **Install Python** (if you don't have it):
   - Download Python 3.7 or higher from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. **Download this app**:
   ```bash
   git clone https://github.com/Gabriel-Benavidez/GroupChat.git
   cd GroupChat
   ```

3. **Set up Python environment**:
   ```bash
   # Create a virtual environment
   python3 -m venv venv

   # Activate it (IMPORTANT - do this every time you run the app):
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate

   # Install required packages (do this after activating venv):
   pip3 install requests python-dotenv
   ```

   Note: If you see a message about updating to zsh shell, you can safely ignore it. This is a macOS system message about the default shell change from bash to zsh. It doesn't affect the application.

4. **Initialize the database**:
   ```bash
   # Make sure your virtual environment is activated first!
   python3 init_db.py
   ```

5. **Start chatting**:
   ```bash
   # Make sure your virtual environment is activated first!
   python3 server.py

   # Open in your browser
   open http://localhost:8090
   ```

   Enter your username and start chatting! Messages are stored locally in the SQLite database.

## Optional: GitHub Integration

If you want your messages to be backed up to GitHub:

1. Create a GitHub Personal Access Token:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Create a new token with 'repo' scope
   - Copy the token

2. Set up GitHub integration:
   ```bash
   # Copy the template file
   cp .env.template .env
   
   # Edit .env and add your token:
   GITHUB_TOKEN=your_token_here
   ```

## Troubleshooting

- **"No module named 'requests'"**:
  ```bash
  # Make sure you've activated the virtual environment:
  source venv/bin/activate  # On Mac/Linux
  venv\Scripts\activate     # On Windows
  
  # Then install the packages:
  pip3 install requests python-dotenv
  ```

- **"Python command not found"**:
  - Make sure Python is installed and added to PATH
  - Try using `python` instead of `python3`

- **"Port already in use"**:
  - Another program is using port 8090
  - Close other applications or change the port in `server.py`

- **"Module not found"**:
  - Make sure you activated the virtual environment
  - Run `pip install -r requirements.txt` again

- **"Database error"**:
  - Delete `database/messages.db`
  - Run `python3 init_db.py` again

- **"GitHub-related errors"**:
  - These can be safely ignored if you haven't set up GitHub integration
  - Messages will still be saved locally

## Features

- Real-time messaging
- Local message storage using SQLite
- Optional GitHub backup
- Multiple user support
- Message history
- Clean, modern interface

## Technical Details

- Built with Python 3.7+
- Uses SQLite for database
- Simple HTTP server
- Optional GitHub integration
- No external dependencies required for basic functionality
