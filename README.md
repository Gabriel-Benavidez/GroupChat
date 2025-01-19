# GroupChat

A real-time group chat application with automatic GitHub backup, multi-user support, and rich interaction features.

## Features

### Core Messaging
- Real-time message sending and receiving
- Clean, modern interface
- Message history preservation
- Automatic GitHub backup of all messages
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
- Automatic backup to GitHub after each message
- Local storage for reactions and user preferences
- SQLite database for message storage
- Git-based version control for message history

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

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/Gabriel-Benavidez/GroupChat.git
   cd GroupChat
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Copy `.env.template` to `.env`
   - Add your GitHub token and repository details

4. Run the server:
   ```bash
   python server.py
   ```

5. Access the application:
   - Open your browser to `http://localhost:8089`
   - Set your username using the styled button in the header
   - Start chatting!

## Usage Guide

### Sending Messages
1. Type your message in the text box at the bottom
2. Press Enter or click Send
3. Messages are automatically backed up to GitHub

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
- Messages are automatically backed up to GitHub
- Full message history is preserved
- Timestamps show when messages were sent

## Technical Details

### Backend
- Python-based HTTP server
- SQLite database for message storage
- Git integration for automatic backups
- Environment variable configuration

### Frontend
- Pure JavaScript (no frameworks)
- LocalStorage for user preferences
- Real-time updates
- Modern CSS styling

### Data Storage
- Messages: SQLite + Git backup
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
