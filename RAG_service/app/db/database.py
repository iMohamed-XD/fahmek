import sqlite3
from typing import Any

from app.schemas import DocumentRead, DocumentType

# import json
# documents = {}

# with open("app/db/data.json") as json_file:
#     data = json.load(json_file)
#     for value in data:
#         documents[value["id"]] = value

# def save():
#     with open("app/db/data.json", "w") as json_file:
#         json.dump(
#             list(documents.values()),
#             json_file
#         )


def get_connection():
    return sqlite3.connect(
        "sqlite.db",
        check_same_thread=False
    )


def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            size INTEGER NOT NULL,
            uploaded_at TEXT NOT NULL,
            type TEXT NOT NULL
        )
    """)
    connection.commit()
    connection.close()


def read_documents():
    connection = get_connection()
    cursor = connection.cursor()
    rows = cursor.execute("""
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


def insert_document(name: str, size: int, uploaded_at: str, type: DocumentType):
    """Insert a new document into the database."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO documents (name, size, uploaded_at, type)
        VALUES (?, ?, ?, ?)
    """, (name, size, uploaded_at, type))
    connection.commit()
    connection.close()
    return cursor.lastrowid


def update_document(
    id: int,
    name: str | None = None,
    size: int | None = None,
    uploaded_at: str | None = None,
    type: DocumentType | None = None
):
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
        connection = get_connection()
        cursor = connection.cursor()

        values.append(id)

        cursor.execute(f"""
            UPDATE documents
            SET {', '.join(updates)}
            WHERE id = ?
        """, values)

        connection.commit()
        connection.close()


def delete_document_sql(id: int):
    """Delete a document from the database."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        DELETE FROM documents
        WHERE id = ?
    """, (id,))
    connection.commit()
    connection.close()


def read_document(id: int | None) -> DocumentRead | None:
    connection = get_connection()
    cursor = connection.cursor()
    if id is None:
        row = cursor.execute("""
            SELECT id, name, size, uploaded_at, type
            FROM documents
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()
    else:
        row = cursor.execute("""
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
