import factory
from datetime import datetime
from app.schemas import DocumentType


class DocumentFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    size = factory.Faker("random_int", min=1, max=150)
    uploaded_at = factory.LazyFunction(
        lambda: datetime.now().isoformat()
    )
    type = factory.Iterator([
        DocumentType.pdf,
        DocumentType.docx
    ])