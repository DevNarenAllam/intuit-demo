from typing import Generator
from sqlmodel import create_engine, Session

from .in_config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, future=True)


# Function to get a session
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
