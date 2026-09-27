# Travel Chat API

Flask backend for [Travel Chat](https://alanmohan.github.io/travel-chat/). It uses the OpenAI Responses API to recommend destinations and activities based on a visitor's preferences and recent chat. Suggestions are recommendations, not booking information; the model has no live travel feed.

## Local setup

Use Python 3.10 or newer. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Paste your OpenAI key into the local `.env` file as `OPENAI_API_KEY=...`. This file is ignored by Git. `OPENAI_MODEL` defaults to `gpt-6-luna` and can be changed there. Start the API with `python app.py`; it listens on port 5000. For production, use `gunicorn app:app --timeout 75`.

## Endpoints

- `GET /health` returns `{ "status": "ok" }`.
- `POST /api/chat` accepts JSON and returns `{ "answer": "...", "label": "Travel recommendations · verify details before booking" }`.

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"budget":2000,"trip_length_days":7,"interests":["food","museums"],"travel_party":"couple","question":"Where should we go?","conversation":[]}'
```

`budget` is a total USD budget from 1 to 100000; `trip_length_days` is 1–90; `interests` contains 1–6 items, each at most 40 characters; `travel_party` is `solo`, `couple`, `friends`, or `family`; `question` is 1–1000 characters. `conversation` is optional and accepts up to 8 recent `{ "role": "user|assistant", "content": "..." }` items of at most 1500 characters each. The frontend sends only the latest 8 messages. Requests over 16 KB receive 413. Responses are limited to 600 model output tokens and 4000 characters.

Errors use `{ "error": { "code": "...", "message": "..." } }` with appropriate HTTP status. A basic per-IP in-memory limit permits 12 requests per minute per worker; production deployments with multiple workers or instances should use a shared limiter. CORS permits `https://alanmohan.github.io` and the local development frontend at port 8113.

## Render Free deployment

Create a Python web service from this public repository. Use build command `pip install -r requirements.txt` and start command `gunicorn app:app --timeout 75`. Choose Free and set `OPENAI_API_KEY` and, optionally, `OPENAI_MODEL` in Render's Environment settings. Never commit `.env`. Render Free may need time to wake after inactivity. The frontend API URL is set in `travel-chat/app.js` in the portfolio repository.

## Privacy and limitations

The frontend keeps chat history only in the current browser tab and sends the latest eight messages with each request. The API does not persist conversations. Rate limiting is memory based and resets on restart. The model does not verify live prices, availability, visa rules, hours, or safety conditions.
