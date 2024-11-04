from sqlmodel import SQLModel, Field, select
from sqlmodel import Session, create_engine
from sqlalchemy.pool import QueuePool
from typing import Generator
from datetime import date


class Players(SQLModel, table=True):
    __tablename__ = "players"

    playerID: str | None = Field(primary_key=True)
    birthYear: int = Field(default=None)
    birthMonth: int = Field(default=None)
    birthDay: int = Field(default=None)
    birthCountry: str = Field(default=None)
    birthState: str = Field(default=None)
    birthCity: str = Field(default=None)
    deathYear: int = Field(default=None)
    deathMonth: int = Field(default=None)
    deathDay: int = Field(default=None)
    deathCountry: str = Field(default=None)
    deathState: str = Field(default=None)
    deathCity: str = Field(default=None)
    nameFirst: str = Field(default=None)
    nameLast: str = Field(default=None)
    nameGiven: str = Field(default=None)
    weight: int = Field(default=None)
    height: int = Field(default=None)
    bats: str = Field(default=None)
    throws: str = Field(default=None)
    debut: date = Field(default=None)
    finalGame: date = Field(default=None)
    retroID: str = Field(default=None)
    bbrefID: str = Field(default=None)


# Replace with your actual database URL
DATABASE_URL = "mysql+pymysql://naren:Python#123@localhost/players"

engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=5, max_overflow=10)


# Function to get a session
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def create_tables():
    SQLModel.metadata.create_all(engine)


# Ensure tables are created before querying
create_tables()


if __name__ == "__main__":
    get_people()
