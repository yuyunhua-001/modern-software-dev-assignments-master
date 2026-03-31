from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def ensure_data_directory_exists() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_directory_exists()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    ensure_data_directory_exists()
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                factor TEXT NOT NULL,
                covered INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (doc_id) REFERENCES notes(id)
            );
            """
        )
        connection.commit()


def insert_note(content: str) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        connection.commit()
        return int(cursor.lastrowid)


def list_notes() -> list[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
        return list(cursor.fetchall())


def get_note(note_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        )
        row = cursor.fetchone()
        return row


def insert_test_factors(factors: list[str], doc_id: Optional[int] = None) -> list[int]:
    with get_connection() as connection:
        cursor = connection.cursor()
        ids: list[int] = []
        for factor in factors:
            cursor.execute(
                "INSERT INTO test_factors (doc_id, factor) VALUES (?, ?)",
                (doc_id, factor),
            )
            ids.append(int(cursor.lastrowid))
        connection.commit()
        return ids


def list_test_factors(doc_id: Optional[int] = None) -> list[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.cursor()
        if doc_id is None:
            cursor.execute(
                "SELECT id, doc_id, factor, covered, created_at FROM test_factors ORDER BY id DESC"
            )
        else:
            cursor.execute(
                "SELECT id, doc_id, factor, covered, created_at FROM test_factors WHERE doc_id = ? ORDER BY id DESC",
                (doc_id,),
            )
        return list(cursor.fetchall())


def mark_test_factor_covered(factor_id: int, covered: bool) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE test_factors SET covered = ? WHERE id = ?",
            (1 if covered else 0, factor_id),
        )
        connection.commit()


