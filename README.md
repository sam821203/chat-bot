# Chatbot

A full-stack AI chatbot with dual-mode conversation (Ask / Agent), LangGraph-based orchestration, and optional Google Search integration for real-time information retrieval.

---

## Overview

This project provides a production-ready conversational AI application with:

- **Ask mode** — Direct LLM responses without external tools; suitable for general Q&A and reasoning.
- **Agent mode** — LLM augmented with a Google Custom Search tool for up-to-date answers on current events, news, and factual queries.

The backend is built with **Flask**, **LangGraph**, and **LangChain**; the frontend is a **Vue 3** SPA with **Vite**. The agent graph conditionally routes between a chatbot node and a tool node based on mode and tool-call decisions.

---

## Features

| Feature | Description |
|--------|-------------|
| **Dual conversation modes** | Toggle between Ask (LLM-only) and Agent (LLM + Google Search). |
| **LangGraph workflow** | State graph with conditional edges: `chatbot` → tools or end; tools → `chatbot` for multi-step tool use. |
| **Trigger-based pre-search** | In Agent mode, user messages containing time/event keywords (e.g. “latest”, “war”, “election”) trigger an optional forced Google Search before the graph runs. |
| **Structured prompts** | System prompts enforce search usage in Agent mode and Markdown-formatted, citation-aware responses. |
| **REST API** | Single `POST /chat` endpoint accepting `messages` and `mode`; returns `response` and `used_search`. |
| **Vue 3 frontend** | Chat UI with Markdown rendering (marked + DOMPurify), mode switcher, and configurable API base URL. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Vite)                                                 │
│  Chat UI, mode toggle, Markdown display, API client                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend (Flask)                                                         │
│  POST /chat → ChatService                                                │
│    → validate request, normalize mode                                    │
│    → optional forced search (SearchTriggerChecker + SearchExecutor)     │
│    → build system prompt (SystemPromptBuilder)                           │
│    → convert client messages → LangChain messages                        │
│    → GraphRunner.invoke(messages, mode)                                  │
│    → extract last AI content → ChatResponse                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LangGraph (graph.py)                                                    │
│  State: { messages, mode }                                               │
│  Nodes: chatbot (LLM; ask = no tools, agent = bind google_search)         │
│  Edges: START → chatbot → conditional → tools | END; tools → chatbot      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            OpenAI Chat (gpt-4o)           Google Custom Search (tools.py)
```

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+ (for frontend)
- **Poetry** (Python dependency management)
- **OpenAI API key**
- **Google Custom Search** API key and Engine ID ([Programmable Search Engine](https://programmablesearchengine.google.com/))

---

## Installation

### Backend

```bash
# Clone the repository
git clone <repository-url>
cd chatbot

# Install Python dependencies with Poetry
poetry install
```

### Frontend

```bash
cd frontend
npm install
```

---

## Configuration

### Backend environment

Copy the example env file and set your keys:

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for the chat model. |
| `OPENAI_MODEL` | No | Model name (default: `gpt-4o`). Use e.g. `gpt-4o-mini` to reduce cost. |
| `GOOGLE_API_KEY` | Yes (Agent mode) | Google Custom Search API key. |
| `GOOGLE_ENGINE_ID` | Yes (Agent mode) | Programmable Search Engine ID. |

### Frontend environment

For local development the frontend uses `http://localhost:10000` by default. For production, set the API base URL:

```bash
cd frontend
cp .env.example .env
# Set VITE_API_BASE=https://your-api-host if not using default
```

---

## Running

### Development

**Terminal 1 — Backend**

```bash
poetry run python app.py
```

Server runs at `http://0.0.0.0:10000`.

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

Access the app at the URL shown by Vite (e.g. `http://localhost:5173`).

### Production

**Backend** (e.g. Gunicorn):

```bash
poetry run gunicorn app:app -b 0.0.0.0:10000
```

**Frontend**: Build and serve the static output:

```bash
cd frontend
npm run build
# Serve frontend/dist with your web server or host on a static/CDN
```

---

## API

### `POST /chat`

Request body (JSON):

| Field | Type | Description |
|-------|------|-------------|
| `messages` | `array` | List of `{ "role": "user"|"assistant", "content": "..." }`. Must be non-empty. |
| `mode` | `string` | `"ask"` or `"agent"`. Default: `"ask"`. |

Response (200):

```json
{
  "response": "Assistant reply text (Markdown supported).",
  "used_search": true
}
```

- `used_search`: `true` if the service performed a forced Google Search before invoking the graph (Agent mode + trigger keywords).

Errors:

- **400** — Validation failure (e.g. missing or empty `messages`); body includes `response` with error message.
- **500** — Server error; body includes `response` with error details.

---

## Deployment

The repo includes a **Render** blueprint (`render.yaml`) for the backend:

- **Runtime**: Python
- **Build**: `poetry install --no-root`
- **Start**: `poetry run gunicorn app:app -b 0.0.0.0:10000`
- **Env**: Configure `OPENAI_API_KEY`, `GOOGLE_API_KEY`, and `GOOGLE_ENGINE_ID` in the Render dashboard.

Deploy the frontend separately (e.g. static site or same host behind a reverse proxy) and set `VITE_API_BASE` to your backend URL at build time.

---

## Project structure

```
chatbot/
├── app.py                 # Flask app, / and /chat routes
├── graph.py               # LangGraph definition (state, nodes, edges)
├── tools.py               # LangChain tools (google_search)
├── services/
│   ├── __init__.py        # create_chat_service factory
│   ├── chat_service.py    # Orchestration: validation, search, prompt, graph, response
│   ├── dto.py             # ChatRequest, ChatResponse, ValidationError
│   ├── graph_runner.py    # GraphRunner protocol and DefaultGraphRunner
│   ├── message_converter.py  # Client ↔ LangChain messages; extract AI content
│   ├── prompt_builder.py  # System prompt from mode, date, search result/error
│   ├── search_executor.py    # SearchExecutor protocol and DefaultSearchExecutor
│   └── search_trigger.py  # Keyword-based forced-search trigger
├── frontend/              # Vue 3 + Vite SPA
│   ├── src/
│   │   ├── App.vue        # Chat UI, mode switch, API calls
│   │   ├── main.js
│   │   └── assets/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── pyproject.toml
├── poetry.lock
├── render.yaml            # Render web service config
└── README.md
```

---

## License

MIT. See repository for details.
