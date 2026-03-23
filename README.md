
# AI Instagram Post Generator

## Features
- FastAPI backend for generating and simulating Instagram posts
- Topic-aware caption generation with tone control (`professional`, `friendly`, `motivational`, etc.)
- Hard validation rules:
  - caption body is capped at 150 words
  - hashtags are normalized and kept in the 5-10 range
- Topic-based hashtag generation (not only generic tags)
- Topic-relevant image generation using external providers:
  - Wikimedia Commons search-first strategy
  - fallback providers if needed
  - safe filename handling and static image storage
- Non-crashing behavior with robust fallbacks when model or network is unavailable
- Real post simulation via HTML Instagram-style preview card
- SQLite-based post storage (`instagram_posts.db`) for persistence across restarts

## Run Instructions

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Endpoints

- `POST /generate-post`
  - Input JSON:
    - `topic` (string)
    - `tone` (string)
  - Generates:
    - caption
    - 5-10 hashtags
    - topic-based image
  - Returns post data + preview metadata + `preview_url`

- `GET /posts`
  - Returns all generated posts from SQLite database.

- `POST /post`
  - Returns simulation payload with all posts and preview objects.

- `GET /preview/latest`
  - Renders the most recent post in an Instagram-style HTML card.

- `GET /preview/{post_index}`
  - Renders a specific post preview by index.

## Open in Browser

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Latest preview: [http://127.0.0.1:8000/preview/latest](http://127.0.0.1:8000/preview/latest)

## How to View Generated Posts

1. Generate a new post from Swagger docs (`POST /generate-post`) or curl.
2. Open all stored posts (JSON):
   - [http://127.0.0.1:8000/posts](http://127.0.0.1:8000/posts)
3. Open the latest visual preview (Instagram-style):
   - [http://127.0.0.1:8000/preview/latest](http://127.0.0.1:8000/preview/latest)
4. Open a specific post preview by index:
   - [http://127.0.0.1:8000/preview/0](http://127.0.0.1:8000/preview/0)
   - change `0` to `1`, `2`, etc.

## Notes

- Images are served from `/static/generated_images/...`.
- If external image services are blocked/unavailable, a fallback image is saved so API flow does not fail.
- Posts are stored in `instagram_posts.db` in the project root.

## Quick curl Test Flow

### 1) Generate a post

```bash
curl -X POST "http://127.0.0.1:8000/generate-post" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI in Healthcare",
    "tone": "professional"
  }'
```

### 2) Get all posts

```bash
curl "http://127.0.0.1:8000/posts"
```

### 3) Get simulation payload

```bash
curl -X POST "http://127.0.0.1:8000/post"
```

### 4) Open visual preview in browser

- Latest post preview: [http://127.0.0.1:8000/preview/latest](http://127.0.0.1:8000/preview/latest)
- Specific preview index example: [http://127.0.0.1:8000/preview/0](http://127.0.0.1:8000/preview/0)

