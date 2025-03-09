# Pseudo-Developer

A Python-based developer assistant application that provides an interactive chat interface with AI-powered code assistance and safe command execution capabilities.

## Features

- Interactive chat interface with AI assistance using OpenAI's API
- Secure command execution within project directories
- Real-time command output display
- Project directory management
- Safe file operations with path validation
- Dark-themed modern UI built with PyQt5
- Support for multiple command types including file operations
- Unicode content handling
- Multi-threaded operation for responsive UI

## Requirements

- Python 3.x
- Dependencies listed in requirements.txt:
  - pytest>=7.4.0
  - pytest-cov>=4.1.0
  - PyQt5>=5.15.9
  - openai>=1.3.5
  - python-dotenv>=1.0.0

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd Pseudo-Developer
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Run the application:
```bash
python -m src.main
```

2. Enter your project directory in the input field and click 'Save'
3. Start chatting with the AI assistant in the message input area
4. View command outputs and execution results in the lower panel

## Development

The project follows clean code principles and is structured for maintainability:

- `src/` - Core application modules
- `tests/` - Comprehensive test suite
- Modern object-oriented design with SOLID principles

### Running Tests

Execute the test suite with coverage reporting:
```bash
python -m tests.run_tests
```

## Security

- All file operations are restricted to the specified project directory
- Path validation prevents directory traversal attacks
- Command execution is limited to safe operations
- Input sanitization for all file operations