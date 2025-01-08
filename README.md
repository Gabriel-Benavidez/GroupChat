# Git-Backed Messaging Application

A simple web-based messaging application that uses Git as a backend storage system. This application allows users to send and receive messages while maintaining a complete history of all communications using Git.

## Features

- Web-based messaging interface
- Git-backed message storage
- Message history with timestamps
- Simple user authentication
- Real-time message updates
- SQLite database for user management
- GitHub API integration for Git operations

## Tech Stack

- Backend: Python (no frameworks)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript (vanilla)
- Version Control: Git
- API: GitHub REST API

## Project Structure

```
.
├── README.md
├── .gitignore
├── .env
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── index.html
│   └── login.html
├── database/
│   └── schema.sql
├── server.py
└── requirements.txt
```

## Important: Environment Setup Required

Before running the application, you must set up your GitHub authentication:

1. Get a GitHub token:
   - Go to: https://github.com/settings/tokens
   - Create new token with scopes: `repo`, `read:discussion`
   - Copy your token

2. Set up environment:
```bash
# Copy the template
cp .env.template .env

# Edit .env and replace your_github_token_here with your actual token
```

3. Install and run:
```bash
pip install -r requirements.txt
python init_db_v2.py
python server.py
```

Visit `http://127.0.0.1:8888` in your browser.

## Note
- Never commit your `.env` file
- Keep your GitHub token secure
- See API documentation below for usage

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
4. Set up your GitHub credentials in `.env` file
5. Initialize the SQLite database:
   ```bash
   python3 init_db.py
   ```
6. Run the server:
   ```bash
   python3 server.py
   ```

## Development

This project is being developed incrementally with the following phases:
1. Basic project setup and structure
2. User authentication system
3. Message storage and retrieval
4. Git integration
5. Real-time updates
6. UI improvements

## Security Notes

- Never commit your `.env` file containing sensitive credentials
- Use environment variables for all sensitive information
- Implement proper input validation and sanitization
- Follow security best practices for user authentication

## License

MIT License
