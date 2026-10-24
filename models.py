import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "tasks.db"

def _serialize_task(row):
    if row is None:
        return None
    task_dict = dict(row)
    task_dict["done"] = bool(task_dict["done"])
    return task_dict


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0

        )
        """
    )
    
    conn.commit()
    conn.close()
    _ensure_created_at_column()

def _ensure_created_at_column():
    conn = get_connection()
    columns = conn.execute("PRAGMA table_info(tasks)").fetchall()
    column_names = [col["name"] for col in columns]
    if "created_at" not in column_names:
        conn.execute("alter table tasks add column created_at TEXT")
        conn.commit()
    conn.close()

def get_all_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [_serialize_task(row) for row in rows]


def get_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return _serialize_task(row)


def create_task(title):
    conn = get_connection()
    created_at = datetime.now().isoformat()
    cur = conn.execute("INSERT INTO tasks (title, done, created_at) VALUES (?, 0, ?)", (title, created_at))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return get_task(task_id)    


def update_task(task_id, title=None, done=None):
    existing = get_task(task_id)
    if not existing:
        return None
    new_title = title if title is not None else existing["title"]
    new_done = int(done) if done is not None else existing["done"]
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id),
    )
    conn.commit()
    conn.close()
    return get_task(task_id)


def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

