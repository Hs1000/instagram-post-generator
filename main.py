
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from agents.content_agent import generate_caption_data
from agents.image_agent import generate_image
from database.db import save_post, get_all_posts, init_db
from models.post import PostRequest
from html import escape

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    init_db()


def _build_preview(post):
    return {
        "username": "ai_creator",
        "display_name": "AI Creator",
        "caption": post["caption"],
        "hashtags": post["hashtags"],
        "image_url": post["image"],
        "topic": post["topic"],
        "word_count": post["word_count"],
        "caption_max_words": 150,
        "hashtag_range": "5-10",
    }


def _preview_html(post):
    caption = escape(post["caption"])
    hashtags = " ".join(post["hashtags"])
    escaped_hashtags = escape(hashtags)
    image_url = "/" + post["image"].lstrip("/")
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Instagram Preview</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      background: #f2f2f2;
      padding: 24px;
    }}
    .card {{
      width: 380px;
      margin: 0 auto;
      background: #fff;
      border: 1px solid #dbdbdb;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 2px 10px rgba(0,0,0,.06);
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px;
      font-weight: 600;
    }}
    .avatar {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: linear-gradient(135deg, #f58529, #dd2a7b, #8134af);
    }}
    img {{
      width: 100%;
      display: block;
      background: #fafafa;
    }}
    .actions {{
      padding: 10px 12px 0;
      color: #262626;
      font-size: 20px;
    }}
    .content {{
      padding: 8px 12px 14px;
      color: #262626;
      line-height: 1.45;
      font-size: 14px;
    }}
    .meta {{
      color: #8e8e8e;
      font-size: 12px;
      margin-top: 6px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="avatar"></div>
      <div>ai_creator</div>
    </div>
    <img src="{image_url}" alt="Generated post image" />
    <div class="actions">♡ &nbsp; 💬 &nbsp; ↗</div>
    <div class="content">
      <strong>ai_creator</strong> {caption}<br/><br/>
      {escaped_hashtags}
      <div class="meta">{post["word_count"]} words</div>
    </div>
  </div>
</body>
</html>
"""


@app.post("/generate-post")
def generate_post(request: PostRequest):
    content_data = generate_caption_data(request.topic, request.tone)
    image_path = generate_image(request.topic)

    post = {
        "topic": request.topic,
        "tone": request.tone,
        "content": content_data["full_text"],
        "caption": content_data["caption"],
        "hashtags": content_data["hashtags"],
        "word_count": content_data["word_count"],
        "image": image_path
    }

    save_post(post)

    return {
        "message": "Post generated successfully",
        "post": post,
        "preview": _build_preview(post),
        "preview_url": "/preview/latest",
    }

@app.get("/posts")
def get_posts():
    return get_all_posts()

@app.post("/post")
def simulate_post():
    posts = get_all_posts()
    previews = [_build_preview(post) for post in posts]
    return {
        "message": "Simulated posting successful",
        "total_posts": len(posts),
        "posts": posts,
        "previews": previews
    }


@app.get("/preview/latest", response_class=HTMLResponse)
def preview_latest():
    posts = get_all_posts()
    if not posts:
        raise HTTPException(status_code=404, detail="No posts available. Generate a post first.")
    return _preview_html(posts[-1])


@app.get("/preview/{post_index}", response_class=HTMLResponse)
def preview_by_index(post_index: int):
    posts = get_all_posts()
    if post_index < 0 or post_index >= len(posts):
        raise HTTPException(status_code=404, detail="Post index not found.")
    return _preview_html(posts[post_index])
