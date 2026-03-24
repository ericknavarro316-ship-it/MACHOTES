import sqlite3
import datetime
import os

DB_NAME = "agenda.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            priority TEXT NOT NULL,
            start_datetime TEXT NOT NULL,
            repeat_days INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            last_notified TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_task(name, priority, start_datetime, repeat_days):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (name, priority, start_datetime, repeat_days, completed)
        VALUES (?, ?, ?, ?, 0)
    """, (name, priority, start_datetime, repeat_days))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, priority, start_datetime, repeat_days, completed, last_notified
        FROM tasks
        ORDER BY start_datetime ASC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def complete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get the task details
    cursor.execute("SELECT repeat_days, start_datetime FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return

    repeat_days = task[0]
    start_datetime_str = task[1]

    if repeat_days > 0:
        # Reschedule task
        start_datetime = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        next_datetime = start_datetime + datetime.timedelta(days=repeat_days)
        next_datetime_str = next_datetime.strftime("%Y-%m-%d %H:%M")

        cursor.execute("UPDATE tasks SET start_datetime = ?, last_notified = NULL WHERE id = ?", (next_datetime_str, task_id))
    else:
        # Mark as completed
        cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))

    conn.commit()
    conn.close()

def update_last_notified(task_id, notified_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET last_notified = ? WHERE id = ?", (notified_time, task_id))
    conn.commit()
    conn.close()

def get_pending_tasks_to_notify():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, priority, start_datetime, repeat_days
        FROM tasks
        WHERE completed = 0 AND (last_notified IS NULL OR last_notified != start_datetime)
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks
