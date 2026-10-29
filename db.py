"""Sauvegarde de l'historique des conversations dans SQLite."""

import os
import sqlite3
from contextlib import closing

DB_PATH = os.getenv("CHATBOT_DB", "chatbot.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with closing(_connect()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'Nouvelle conversation',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL
                    REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conv
                ON messages(conversation_id);
            """
        )


def create_conversation(title: str = "Nouvelle conversation") -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute("INSERT INTO conversations (title) VALUES (?)", (title,))
        return cur.lastrowid


def list_conversations() -> list[dict]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def rename_conversation(conv_id: int, title: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id)
        )


def delete_conversation(conv_id: int) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))


def add_message(conv_id: int, role: str, content: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conv_id, role, content),
        )


def get_messages(conv_id: int) -> list[dict]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
            (conv_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_messages(conv_id: int) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))