# AI-Chatbot (Django + OpenAI)

Lightweight ChatGPT-style web chat built with Django that connects to the OpenAI Chat Completions API. The API key is stored in `.env` and never exposed to the browser. The UI preserves conversation context and sends it to the backend each turn.

## Features

- Modes landing page at `/` to choose specialized assistants
- ChatGPT-like interface (Tailwind UI) at `/chat/`
- Backend proxy to OpenAI (no API key in the browser)
- Conversation context (messages array) per request
- Configurable model and temperature
- Basic error handling and typing indicator

## Requirements

- Python 3.10+
- An OpenAI API key

Install Python packages from `requirements.txt`:

```
pip install -r requirements.txt
```

## Configuration

Create a `.env` file at the project root with your key:

```
OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY
# Optional (defaults to gpt-4o-mini if not set)
# OPENAI_MODEL=gpt-4o-mini
```

Environment variables are loaded in `config/settings.py` via `python-dotenv`.

## Run

```
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` to select a mode, then you will be redirected to `/chat/` with the chosen assistant.

## Endpoints

- `GET /` → Renders modes selector (`templates/modes.html`).
- `GET /chat/` → Renders the chat UI (`templates/chat.html`).
- `POST /api/chat/` → Forwards the conversation to OpenAI and returns the assistant reply.
- `GET /api/modes/` → Returns the modes/assistants catalog.

Request body (example):

```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "assistant_id": "teacher_tutor",
  "model": "gpt-4o-mini",
  "temperature": 0.7
}
```

Response body (example):

```json
{
  "reply": "Hi there! How can I help you today?"
}
```

## Key Files

- `config/settings.py` – loads `.env`, registers `app`, templates, static dirs
- `config/urls.py` – routes `/` and `/api/chat/` via `app.urls`
- `app/urls.py` – maps `''` to `chat_page` and `api/chat/` to `chat_api`
- `app/views.py` – OpenAI call in `chat_api`, renders UI in `chat_page`
- `templates/chat.html` – chat frontend calling `/api/chat/`

## Notes

- The API view is CSRF-exempt for simplicity. If you add auth, restore CSRF accordingly.
- Streaming responses are not implemented; the UI shows a typing indicator while waiting for the backend.
- Static files are served from `static/` in development; tailor as needed for production.

## Troubleshooting

- 500 with `Server missing OPENAI_API_KEY`: Ensure `.env` exists and the key is valid.
- 401 from OpenAI: Check that your API key is active and has quota.
- Import errors: Reinstall deps with `pip install -r requirements.txt` and ensure the correct Python is used.