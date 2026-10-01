"""Tasks in one SQLite file. Every query is scoped to a chat, so one user never sees or
changes another user's tasks, even with a forged button press."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL,
    title      TEXT    NOT NULL,
    done       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS tasks_chat ON tasks (chat_id);
"""


@dataclass(frozen=True)
class Task:
    id: int
    chat_id: int
    title: str
    done: bool


class TaskStore:
    def __init__(self, path: str | Path) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    def add(self, chat_id: int, title: str) -> Task:
        with self._db:
            cur = self._db.execute(
                "INSERT INTO tasks (chat_id, title) VALUES (?, ?)", (chat_id, title))
        return Task(cur.lastrowid, chat_id, title, False)

    def list(self, chat_id: int) -> list[Task]:
        """Open tasks first, then done ones, each group oldest first."""
        rows = self._db.execute(
            "SELECT id, chat_id, title, done FROM tasks WHERE chat_id = ? ORDER BY done, id",
            (chat_id,)).fetchall()
        return [Task(r["id"], r["chat_id"], r["title"], bool(r["done"])) for r in rows]

    def count(self, chat_id: int) -> int:
        return self._db.execute(
            "SELECT COUNT(*) FROM tasks WHERE chat_id = ?", (chat_id,)).fetchone()[0]

    def count_open(self, chat_id: int) -> int:
        return self._db.execute(
            "SELECT COUNT(*) FROM tasks WHERE chat_id = ? AND done = 0", (chat_id,)).fetchone()[0]

    def toggle(self, chat_id: int, task_id: int) -> Task | None:
        """Flip a task between open and done. None if this chat has no such task."""
        with self._db:
            cur = self._db.execute(
                "UPDATE tasks SET done = 1 - done WHERE id = ? AND chat_id = ?", (task_id, chat_id))
        if cur.rowcount == 0:
            return None
        r = self._db.execute(
            "SELECT id, chat_id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return Task(r["id"], r["chat_id"], r["title"], bool(r["done"]))

    def delete(self, chat_id: int, task_id: int) -> bool:
        with self._db:
            cur = self._db.execute(
                "DELETE FROM tasks WHERE id = ? AND chat_id = ?", (task_id, chat_id))
        return cur.rowcount > 0

    def clear_done(self, chat_id: int) -> int:
        """Remove this chat's done tasks; returns how many went."""
        with self._db:
            cur = self._db.execute(
                "DELETE FROM tasks WHERE chat_id = ? AND done = 1", (chat_id,))
        return cur.rowcount
