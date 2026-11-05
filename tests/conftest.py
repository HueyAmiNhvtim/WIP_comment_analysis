# Where the fixtures - stuff that can be used by all tests in the suite unless specified otherwise.
# There's also other stuff like external pluging loading, hooks test root path, etc. We will get there when we get there I think.

import pytest
from src.data.database_manager import DatabaseManager


@pytest.fixture
def db_manager():
    """
    Creates all them tables on the running Postgres testing container.
    The port is specified in the corresponding docker-compose file
    Runs only once per test session
    """
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
    with db_manager.session_scope() as session:
        yield session
        # session_scope will auto close upon exiting the with statement.