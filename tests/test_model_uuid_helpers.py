import uuid

from app.models.review import new_uuid as review_new_uuid
from app.models.synopsis_moderation import new_uuid as moderation_new_uuid


def test_review_new_uuid_returns_valid_uuid_string():
    value = review_new_uuid()

    assert isinstance(value, str)
    assert str(uuid.UUID(value)) == value


def test_synopsis_moderation_new_uuid_returns_valid_uuid_string():
    value = moderation_new_uuid()

    assert isinstance(value, str)
    assert str(uuid.UUID(value)) == value
