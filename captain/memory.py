import sqlite3
import time


class Memory:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT, created REAL)")
        path.chmod(0o600)

    def add(self, text):
        if len(text) > 2000:
            raise ValueError("Memory note is too long")
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO notes(text,created) VALUES (?,?)", (text, time.time()))

    def list(self):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT id,text FROM notes ORDER BY id DESC LIMIT 30").fetchall()

    def clear(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM notes")
