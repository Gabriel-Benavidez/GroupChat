# GroupChat

A real-time group chat application with optional GitHub backup, multi-user support, and rich interaction features.

## Features

### Core Messaging
- Real-time message sending and receiving
- Clean, modern interface
- Message history preservation
- Optional automatic GitHub backup of all messages
- Automatic timestamps on messages

### User Management
- Customizable usernames
- Username persistence across page refreshes
- No login required - just set your name and start chatting
- Username history tracking for reactions

### Rich Reactions System
- Multiple emoji reactions per message
- Support for multiple reactions from the same user
- Reaction history preservation
- Detailed reaction tooltips showing who reacted with what
- Reaction counts for each emoji type
- Available emojis: 👍 ❤️ 😊 🎉 👏 🚀 😢 😂 🤔

### Data Storage & Backup
- Local SQLite database for message storage
- Optional GitHub integration for automatic backup
- Local storage for reactions and user preferences
- Git-based version control (when GitHub is configured)

### User Interface
- Modern, clean design with gradient effects and animations
- Polished header with dynamic styling
- Responsive layout that adapts to different screen sizes
- Real-time updates with smooth transitions
- Loading indicators and visual feedback
- Error notifications with fade effects
- Success confirmations
- Enhanced username display with overflow handling
- Improved message input area
- Subtle shadows and depth effects

## Quick Start Guide

Just want to get chatting? Follow these simple steps:

1. **Install Python** (if you don't have it):
   - Download Python 3.7 or higher from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. **Download this app**:
   ```bash
   git clone https://github.com/Gabriel-Benavidez/GroupChat.git
   cd GroupChat
   ```

3. **Set up the app**:
   ```bash
   # Create a virtual environment
   python3 -m venv venv

   # Activate it:
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate

   # Install required packages
   pip install -r requirements.txt

   # Initialize the database
   python3 init_db.py
   ```

4. **Start the chat**:
   ```bash
   python3 server.py
   ```

5. **Open in your browser**:
   - Go to: http://localhost:8089
   - Enter your username
   - Start chatting!

That's it! The app is now running on your computer. Messages will be stored locally in the SQLite database.

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

3. Configure Git (if not already set):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

The app will work perfectly fine without GitHub integration - your messages will still be saved locally.

## Troubleshooting Common Issues

- **"Python command not found"**:
  - Make sure Python is installed and added to PATH
  - Try using `python` instead of `python3`

- **"Port already in use"**:
  - Another program is using port 8089
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

For more detailed setup instructions and features, read on below.

## Getting Started

### Prerequisites
1. Make sure you have Python 3.7+ installed:
   ```bash
   # On macOS
   brew install python3
   
   # On Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   
   # On Windows
   # Download and install from https://www.python.org/downloads/
   ```

2. Verify Python installation:
   ```bash
   python3 --version
   # Should show Python 3.7 or higher
   ```

3. (Optional) If you want to use GitHub backup:
   ```bash
   # Configure Git user
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Gabriel-Benavidez/GroupChat.git
   cd GroupChat
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python3 init_db.py
   ```

5. (Optional) Set up GitHub integration:
   ```bash
   # Copy the template file
   cp .env.template .env
   
   # Edit .env file with your GitHub details
   # Replace these values with your own:
   GITHUB_TOKEN=your_token_here
   
   # If you skip this step, the app will work without GitHub backup
   ```

### Running the Application
1. Start the server:
   ```bash
   python3 server.py
   ```

2. Access the application:
   - Open your browser to `http://localhost:8089`
   - Set your username using the styled button in the header
   - Start chatting!

### Troubleshooting
- If you see "command not found" errors, make sure Python is installed and in your PATH
- If you get syntax errors, ensure you're using Python 3.7 or higher
- If you see Git-related errors, they can be safely ignored if you haven't set up GitHub integration
- If the database fails to initialize, check that you have write permissions in the directory
- For any other issues, please check the GitHub issues page or create a new issue

## Usage Guide

### Sending Messages
1. Type your message in the text box at the bottom
2. Press Enter or click Send
3. Messages are automatically stored in the local database

### Setting Your Username
1. Click the "Username" button in the header area
2. Enter your desired username in the modal
3. Click Save to apply
4. Your username is displayed in a clean, pill-shaped container
5. Long usernames are gracefully truncated with ellipsis

### Using Reactions
1. Hover over any message
2. Click the "React" button
3. Choose an emoji from the popup menu
4. View reactions by hovering over the emoji
5. Multiple reactions per user are supported
6. Reaction history is preserved even when changing usernames

### Message History
- All messages are stored in SQLite database
- Messages are optionally backed up to GitHub
- Full message history is preserved
- Timestamps show when messages were sent

## Technical Details

### Backend
- Python-based HTTP server
- SQLite database for message storage
- Optional Git integration for automatic backups
- Environment variable configuration

### Frontend
- Pure JavaScript (no frameworks)
- LocalStorage for user preferences
- Real-time updates
- Modern CSS styling

### Data Storage
- Messages: SQLite + optional Git backup
- Reactions: LocalStorage
- User preferences: LocalStorage
- Username history: Preserved with reactions

## Security Features
- No sensitive data storage
- GitHub token protection
- SQLite database security
- Cross-site scripting protection

## Contributing
Feel free to submit issues and enhancement requests!

## License
MIT License - See LICENSE file for details
