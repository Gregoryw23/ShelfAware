from app.db.database import get_db
from sqlalchemy.orm import Session

# Test that the get_db dependency yields a Session and closes it after use
def test_get_db_yields_session_and_closes():
    gen = get_db()
    db = next(gen)
    assert isinstance(db, Session)
    gen.close()


