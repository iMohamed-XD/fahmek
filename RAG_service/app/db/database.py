import sqlite3
from typing import Any, Generator
from contextlib import contextmanager

from app.schemas import DocumentRead, DocumentType


class DataBase:
    def __init__(self):
        self.connection = sqlite3.connect(
            "sqlite.db",
            check_same_thread=False
        )
        self.cursor = self.connection.cursor()

    def get_connection(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError("Failed to establish a database connection")
        return self.connection

    def init_db(self) -> None:
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def read_documents(self) -> dict[int, DocumentRead]:
        rows = self.cursor.execute("""
            SELECT id, name, size, uploaded_at, type
            FROM documents
        """).fetchall()

        return {
            row[0]: DocumentRead(
                id=row[0],
                name=row[1],
                size=row[2],
                uploaded_at=row[3],
                type=row[4],
            )
            for row in rows
        }

    def insert_document(self, name: str, size: int, uploaded_at: str, type: DocumentType) -> int | None:
        """Insert a new document into the database."""
        self.cursor.execute("""
            INSERT INTO documents (name, size, uploaded_at, type)
            VALUES (?, ?, ?, ?)
        """, (name, size, uploaded_at, type))
        new_id = self.cursor.lastrowid
        self.connection.commit()
        return new_id

    def update_document(
        self,
        id: int,
        name: str | None = None,
        size: int | None = None,
        uploaded_at: str | None = None,
        type: DocumentType | None = None
    ) -> None:
        updates: list[str] = []
        values: list[Any] = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)

        if size is not None:
            updates.append("size = ?")
            values.append(size)

        if uploaded_at is not None:
            updates.append("uploaded_at = ?")
            values.append(uploaded_at)

        if type is not None:
            updates.append("type = ?")
            values.append(type)

        if updates:
            values.append(id)

            self.cursor.execute(f"""
                UPDATE documents
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)

            self.connection.commit()

    def delete_document_sql(self, id: int) -> None:
        """Delete a document from the database."""
        self.cursor.execute("""
            DELETE FROM documents
            WHERE id = ?
        """, (id,))
        self.connection.commit()

    def read_document(self, id: int | None) -> DocumentRead | None:
        if id is None:
            row = self.cursor.execute("""
                SELECT id, name, size, uploaded_at, type
                FROM documents
                ORDER BY id DESC
                LIMIT 1
            """).fetchone()
        else:
            row = self.cursor.execute("""
                SELECT id, name, size, uploaded_at, type
                FROM documents
                WHERE id = ?
            """, (id,)).fetchone()

        if row is None:
            return None

        return DocumentRead(
            id=row[0],
            name=row[1],
            size=row[2],
            uploaded_at=row[3],
            type=row[4],
        )

    def __enter__(self):
        self.connection = sqlite3.connect(
        "sqlite.db",
        check_same_thread=False
    )
        self.cursor = self.connection.cursor()
        self.init_db()
        return self

    def __exit__(self, *args):
        self.connection.close()


@contextmanager
def managed_db() -> Generator[DataBase, None, None]:
    """Context manager for managing the database connection."""
    with DataBase() as db:
        db.init_db()

        yield db

        db.connection.close()