import uuid

from app.models.book import new_uuid


def test_new_uuid_returns_valid_uuid_string():
    value = new_uuid()

    assert isinstance(value, str)
    assert str(uuid.UUID(value)) == value
