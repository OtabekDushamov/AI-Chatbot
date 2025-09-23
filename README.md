# AI-Chatbot

## Setup

1. Create a `.env` file at project root:

```
OPENAI_API_KEY=sk-...
# Optional
# OPENAI_MODEL=gpt-4o-mini
```

2. Install dependencies and run migrations:

```
pip install -r requirements.txt
python manage.py migrate
```

3. Run the server:

```
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and start chatting.