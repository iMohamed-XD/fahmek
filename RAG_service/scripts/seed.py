import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from app.db.database import insert_document
from app.db.factory import DocumentFactory

for _ in range(20):
    document = DocumentFactory()

    insert_document(
        name=document["name"],
        size=document["size"],
        uploaded_at=document["uploaded_at"],
        type=document["type"],
    )