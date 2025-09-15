# ChatAgent

ChatAgent is a lightweight conversational AI application designed to integrate with various language model providers and external tools. It provides a flexible and extensible framework for building agent-based interactions with human-in-the-loop capabilities.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Human-in-the-Loop Workflow](#human-in-the-loop-workflow)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

- REST API interface via FastAPI
- Support for multiple LLM providers (Ollama, with extensible architecture for OpenAI, Anthropic, etc.)
- Integration with Tavily search tool
- Modular agent architecture (ReAct pattern implemented)
- Human-in-the-loop workflow for tool execution with confirmation dialogs
- Real-time streaming responses using Server-Sent Events (SSE)
- Web-based chat interface with model switching capabilities

## Technology Stack

- **Backend**: Python, FastAPI, LangChain, LangGraph
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **AI/ML**: Ollama (primary), with support for extension to other providers
- **Tools**: Tavily search API
- **Deployment**: Uvicorn

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Virtual environment tool (venv or virtualenv)
- Ollama (for local LLM support)
- Tavily API key (for search functionality)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd chatagent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root with the following variables:
   ```env
   TAVILY_API_KEY=your_tavily_api_key_here
   OLLAMA_BASE_URL=http://localhost:11434  # Default Ollama URL
   ```

2. Ensure Ollama is running and the required models are pulled:
   ```bash
   ollama pull qwen3:8b  # Or any other model you want to use
   ```

## Usage

### Development Server

Start the development server with hot reloading:
```bash
uvicorn main:app --reload
```

### Production Server

Start the production server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`.

## API Endpoints

### `GET /`

Serves the main chat interface (HTML page).

### `GET /models`

Returns a list of available models grouped by provider.

**Response:**
```json
{
  "ollama": ["qwen3:8b", "llama3:8b", ...],
  "deepseek": ["deepseek-chat", ...]
}
```

### `POST /chat`

Processes chat messages and streams responses.

**Request Body:**
```json
{
  "text": "Your message here",
  "provider": "ollama",
  "model": "qwen3:8b",
  "thread_id": "optional-uuid"
}
```

**Response:**
Streams Server-Sent Events with different message types:
- `thought`: Processing status updates
- `content`: AI-generated content
- `tool_request`: Tool execution requests requiring human confirmation
- `tool_result`: Results from executed tools

### `POST /continue_thread`

Continues execution after human approval of tool requests.

**Request Body:**
```json
{
  "thread_id": "uuid",
  "approved": true,
  "tool_calls": [
    {
      "name": "tool_name",
      "args": { "param1": "value1" }
    }
  ]
}
```

## Project Structure

```
chatagent/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in version control)
├── .gitignore              # Git ignore file
├── README.md               # This file
├── src/
│   ├── index.html          # Chat interface
│   ├── models/             # Language model provider implementations
│   │   ├── __init__.py
│   │   ├── ollama_provider.py
│   │   └── deepseek_provider.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── tavily.py       # Tavily search tool integration
│   └── agent/
│       ├── __init__.py
│       └── react.py        # ReAct agent pattern implementation
└── test/
    └── test_interrupt.py   # Test script for human-in-the-loop workflow
```

## Human-in-the-Loop Workflow

The ChatAgent implements a human-in-the-loop workflow for tool execution to ensure safety and user control:

1. **Agent Processing**: When the AI agent determines a tool needs to be executed, it interrupts before the actual execution.

2. **Tool Request**: The system sends a `tool_request` message to the frontend containing:
   - Tool name
   - Tool parameters

3. **User Confirmation**: The frontend displays a confirmation dialog showing:
   - Tool name
   - Tool parameters (editable)
   - Approve/Reject buttons

4. **User Action**: The user can either:
   - Approve the tool execution (with optional parameter editing)
   - Reject the tool execution

5. **Execution Continuation**: 
   - If approved, the tool is executed and results are processed
   - If rejected, the agent continues without tool execution

6. **Result Processing**: The tool results are incorporated into the agent's response generation.

This workflow ensures that potentially sensitive or costly tool operations require explicit user approval before execution.

## Testing

### Automated Testing

Run the test script to verify the human-in-the-loop workflow:
```bash
python test/test_interrupt.py
```

This script:
1. Sends a chat message that triggers a tool call
2. Verifies the tool request is properly sent
3. Simulates user approval
4. Verifies the tool execution and result processing

### Manual Testing

1. Start the server: `uvicorn main:app --reload`
2. Open `http://localhost:8000` in your browser
3. Send a message that would trigger a tool call (e.g., "Search for information about artificial intelligence")
4. Observe the tool confirmation dialog
5. Approve or reject the tool execution
6. Verify the response behavior

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature-name`
5. Create a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

1. **"Module not found" errors**: Ensure you've activated your virtual environment and installed all dependencies.

2. **Ollama connection errors**: Verify Ollama is running and accessible at the configured URL.

3. **Tavily API errors**: Check that your TAVILY_API_KEY is correctly set in the `.env` file.

4. **Tool execution not interrupting**: Ensure you're using `create_react_agent` with `interrupt_before=["tools"]` parameter.

### Debugging Tips

1. Check the terminal output for error messages
2. Use browser developer tools to inspect network requests
3. Add logging statements to trace execution flow
4. Verify the thread_id is consistent between requests

## Architecture Notes

### Backend Architecture

The backend follows a modular monolith pattern with the following key components:

1. **FastAPI Layer**: Handles HTTP requests and responses
2. **Model Providers**: Abstract different LLM providers (Ollama, DeepSeek, etc.)
3. **Tools**: External integrations (Tavily search)
4. **Agent Logic**: Orchestrates interactions using LangGraph
5. **State Management**: Uses LangGraph's checkpointer for conversation state

### Frontend Architecture

The frontend is a single-page application with:

1. **Chat Interface**: Real-time messaging with streaming responses
2. **Model Selection**: Dynamic provider and model switching
3. **Tool Confirmation**: Modal dialogs for human-in-the-loop workflow
4. **State Management**: Client-side tracking of conversation state

### Data Flow

1. User sends message via frontend
2. Frontend POSTs to `/chat` endpoint
3. Backend initializes agent with selected model
4. Agent processes message, potentially requesting tool execution
5. If tool execution is needed, agent interrupts and sends tool request
6. Backend streams tool request to frontend
7. Frontend displays confirmation dialog
8. User approves/rejects tool execution
9. Frontend POSTs to `/continue_thread` with user decision
10. Backend resumes agent execution based on user input
11. Agent completes processing and generates final response
12. Backend streams final response to frontend
13. Frontend displays response to user

This architecture ensures a responsive user experience while maintaining proper separation of concerns between components.
