# Where the fixtures - stuff that can be used by all tests in the suite unless specified otherwise.
# There's also other stuff like external pluging loading, hooks test root path, etc. We will get there when we get there I think.

import pytest
from src.data.database_manager import DatabaseManager
from unittest.mock import MagicMock

from src.extractor.youtube_extractor import YoutubeExtractor

@pytest.fixture
def mock_youtube_client():
    """Provides a fresh MagicMock pretending to be the Google YouTube API client."""
    return MagicMock()


@pytest.fixture
def ytb_extractor(mock_youtube_client):
    """Provides a YoutubeExtractor injected with the mocked client."""
    return YoutubeExtractor(youtube_client=mock_youtube_client)


@pytest.fixture(scope="session")
def db_manager():
    """
    Creates all them tables on the running Postgres testing container.
    The port is specified in the corresponding docker-compose file
    Runs only once per test session
    """
    
    # Fun behaviour: pytest will treat the fixture with yield as a two-phase lifescycle.
    # Everything before yield is treated as a setup, and everything after is treated as a teardown.
    manager = DatabaseManager(env_path=".env.test", echo=False)
    manager.initialize_tables()
    yield manager  # Generator so that when calling this thing again after yielding, 
                   # this will delete the tables and subsequently close the db manager instance
    
    # Cleans up tables when all tests finish.
    manager.delete_tables()
    manager.close()


@pytest.fixture
def session(db_manager: DatabaseManager):
    """Provides a fresh transactional session for each individual test,
        and rolls back changes after the test finishes to prevent cross-test data contamination.

    Args:
        db_manager (DatabaseManager): Database Manager
    """
    session = db_manager.session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # session_scope will auto close upon exiting the with statement.