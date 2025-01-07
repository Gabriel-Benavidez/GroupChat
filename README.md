# Basic Chat Application

A simple real-time chat application that allows users to communicate with each other in a shared chat room.

## Features

- Real-time messaging
- Simple and intuitive user interface
- Support for multiple users
- Message timestamps
- Clean and modern design

## Technologies Used

- Frontend:
  - HTML5
  - CSS3
  - JavaScript
  - WebSocket for real-time communication

- Backend:
  - Python
  - Flask (Web framework)
  - Flask-SocketIO (WebSocket support)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd basic-chat
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
basic-chat/
├── app.py              # Main application file
├── static/
│   ├── css/           # Stylesheets
│   │   └── style.css
│   └── js/            # JavaScript files
│       └── main.js
├── templates/         # HTML templates
│   └── index.html
├── requirements.txt   # Python dependencies
└── README.md         # Project documentation
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For any questions or feedback, please open an issue in the repository.
