
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "instagram_posts.db"


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                tone TEXT NOT NULL,
                content TEXT NOT NULL,
                caption TEXT NOT NULL,
                hashtags TEXT NOT NULL,
                word_count INTEGER NOT NULL,
                image TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_post(post):
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO posts (topic, tone, content, caption, hashtags, word_count, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post["topic"],
                post["tone"],
                post["content"],
                post["caption"],
                json.dumps(post["hashtags"]),
                int(post["word_count"]),
                post["image"],
            ),
        )
        conn.commit()


def get_all_posts():
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT topic, tone, content, caption, hashtags, word_count, image
            FROM posts
            ORDER BY id ASC
            """
        ).fetchall()

    posts = []
    for row in rows:
        posts.append(
            {
                "topic": row["topic"],
                "tone": row["tone"],
                "content": row["content"],
                "caption": row["caption"],
                "hashtags": json.loads(row["hashtags"]),
                "word_count": row["word_count"],
                "image": row["image"],
            }
        )
    return posts
