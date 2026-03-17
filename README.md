# Agent Creator - Dynamic Code Generation API for Multi-Agent Systems
https://www.mechsai.com/

Agent Creator  is a robust FastAPI-based service designed to dynamically generate Python code and directory structures for AI agents. By sending a JSON payload describing your agent topology, this API automatically scaffolds the necessary folders, `.env` files, and executable `agent.py` scripts complete with tool integrations, LLM provider configurations, and nested sub-agents.

## ✨ Features

* **Dynamic Code Generation:** Automatically writes `agent.py` files using AST/String manipulation based on your configurations.
* **Multi-Provider Support:** Supports Gemini, Anthropic, OpenAI, and Deepseek natively (utilizing LiteLLM).
* **Complex Topologies:** Compose LLM Agents, Sequential Agents, and Parallel Agents with nested hierarchies.
* **Extensive Tool Integrations:** Built-in support for Yahoo Finance, Brave Search, EXA Search, Serper, Hyperbrowser, and Model Context Protocol (MCP) tools.
* **Secure & Isolated:** Creates isolated directories and environment variables for each main agent workspace.

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* `pip` package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agent-creator-api.git
   cd agent-creator-api
   ```

2. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn python-dotenv yfinance langchain_community crewai_tools hyperbrowser
   ```
   *(Note: Ensure you have your `google.adk` module available in your environment as referenced in the code).*

3. Set up your environment variables by creating a `.env` file in the root directory:
   ```env
   AGENT_DIR=/path/to/your/output/directory
   PORT=8080
   ```

4. Run the server:
   ```bash
   python main.py
   # Or using uvicorn directly:
   # uvicorn main:app --host 0.0.0.0 --port 8080
   ```

## 📖 API Documentation

### 1. Create an Agent Directory
**Endpoint:** `POST /agent_creator`

Scaffolds a complete agent directory structure including `__init__.py`, `.env` with provided API keys, and the fully coded `agent.py`.

#### **Input Format**

The API expects a JSON payload containing a **stringified JSON array** of your agent configurations. It supports two payload structures:

**Option A: Simple Structure**
```json
{
  "text": "[{\"type\": \"Multi Agent\", \"name\": \"FinanceBot\", \"provider\": \"openai\", \"model\": \"gpt-4o\", \"apiKey\": \"sk-...\", \"description\": \"A bot that analyzes finance\", \"connected_agents\": []}]"
}
```

**Option B: Nested Structure (e.g., from specific frontend chat interfaces)**
```json
{
  "new_message": {
    "parts": [
      {
        "text": "[{\"type\": \"Multi Agent\", \"name\": \"FinanceBot\", ...}]"
      }
    ]
  }
}
```

#### **The Inner Agent Configuration Schema (The Stringified JSON)**

Here is what the actual agent configuration objects should look like before being stringified into the `text` field:

```json
[
  {
    "type": "Multi Agent",
    "name": "ResearchCoordinator",
    "provider": "anthropic",
    "model": "claude-3-opus-20240229",
    "apiKey": "sk-ant-...",
    "description": "Coordinates research tasks between sub-agents.",
    "instructions": [
      "You are the lead researcher.",
      "Delegate search tasks to your sub-agents."
    ],
    "connected_agents": [
      {
        "type": "LLM Agent",
        "name": "WebScraperAgent",
        "provider": "openai",
        "model": "gpt-4o",
        "instruction": "Scrape websites and summarize findings.",
        "tools": ["ScrapeWebsiteTool", "BraveSearchTool"],
        "BraveSearchAPIKey": "brave-key-123"
      },
      {
        "type": "Parallel agent",
        "name": "DataProcessingSquad",
        "description": "Processes data in parallel",
        "connected_agents": [
          {
            "type": "LLM Agent",
            "name": "StockAnalyzer",
            "tools": ["get_price", "YahooFinanceNewsTool"]
          }
        ]
      }
    ]
  }
]
```

#### **Response**

**Success (200 OK):**
```json
{
  "message": "Agent directory structure created successfully",
  "agents_processed": 1,
  "result": null
}
```

**Error (400 Bad Request - Invalid JSON):**
```json
{
  "detail": "Invalid JSON in text field: Expecting value: line 1 column 1 (char 0)"
}
```

### 2. Delete an Agent Folder
**Endpoint:** `DELETE /delete_folder/{folder_name}`

Safely removes a generated agent folder and all its contents.

**Path Parameters:**
* `folder_name` (string): The name of the folder inside your `AGENT_DIR` to delete.

**Response (200 OK):**
```json
{
  "message": "Folder 'FinanceBot' has been deleted successfully"
}
```
*(Note: Attempting to delete the root `agent_creator` folder is protected and will return a 403 Forbidden).*

### 3. Health Check
**Endpoint:** `GET /healthz`

Returns a simple `200 OK` status to verify the API is running.

## 📂 Generated Output Structure

If you send a valid `POST /agent_creator` request with a multi-agent named `ResearchCoordinator`, the API will generate the following file system structure inside your `AGENT_DIR`:

```text
/your_base_agent_dir
└── /ResearchCoordinator
    ├── __init__.py           # Makes the directory a Python module
    ├── .env                  # Auto-generated with your specified API keys (e.g., ANTHROPIC_API_KEY, BRAVE_API_KEY)
    └── agent.py              # The executable Python script defining your agents, tools, and LiteLLM configurations
```