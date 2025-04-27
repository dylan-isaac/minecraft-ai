from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

# Define the SQLite database file path
# TODO: Consider making this configurable via environment variables
SQLITE_FILE_NAME = "minecraft_data.db"
DATABASE_URL = f"sqlite:///{SQLITE_FILE_NAME}"

# Create the database engine
# connect_args is needed for SQLite to support features like alembic later
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Creates the database and all tables defined in SQLModel models."""
    # This function should be called once on application startup
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency function to get a database session."""
    with Session(engine) as session:
        yield session
