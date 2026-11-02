import pytest
from src.data.user_repository import UserRepository
from src.data.models import Users

from sqlalchemy.orm import Session


def test_user_insert(session: Session):
    """Test inserting a single record in the user repository

    Args:
        session (Session): SQLAlchemy session that handles the Python's side of database operations
    """
    test_id = "ytb_kontio_yahoo_420"
    repo = UserRepository(session=session)
    user = Users(platform_user_id=test_id)
    
    saved_user = repo.insert(user)
    session.flush()
    
    assert saved_user.id is not None # Check that the user is inserted
    
    fetched_results = repo.get_by(platform_user_id=test_id)
    
    assert len(fetched_results) == 1 # Check that the user is inserted only once.
    assert fetched_results[0].platform_user_id == test_id
    assert fetched_results[0].platform_user_id == saved_user.platform_user_id
    
    
def test_ensure_users_exist(session):
    """Test the pipeline helper that resolves string IDs into UUIDs.
    Args:
        session (Session): SQLAlchemy session that handles the Python's side of database operations
    """
    repo = UserRepository(session)
    
    incoming_ids = ["twct_MAR_dunn", "twct_MAR_park", "twct_MAR_jae"]
    user_map = repo.ensure_users_exist(incoming_ids)
    
    assert len(user_map) == 3
    for uid in incoming_ids:
        assert uid in user_map
        assert user_map[uid] is not None  # Has a valid UUID!
        
    # Re-running with existing + 1 new should not duplicate existing records in the database
    second_run_ids = ["twct_MAR_park", "twct_141_gaz"]
    second_map = repo.ensure_users_exist(second_run_ids)
    
    assert second_map["twct_MAR_park"] == user_map["twct_MAR_park"]  # Kept original UUID
    assert "twct_141_gaz" in second_map                              # Ensure the new one is included