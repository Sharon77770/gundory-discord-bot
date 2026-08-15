from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.models import MilitaryEvent


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture()
def event_factory():
    def make(user_id, start, end=None, event_type="LEAVE", title="휴가"):
        return MilitaryEvent(guild_id=1, discord_user_id=user_id, event_type=event_type,
                             title=title, start_date=start, end_date=end)
    return make

