from src.data.user_repository import UserRepository
from src.data.comment_repository import CommentRepository
from src.data.livechat_repository import LivechatRepository
from src.data.video_repository import VideoRepository

from datetime import datetime, timezone

from src.data.models import Users, Videos, LiveComments, Comments
from sqlalchemy.orm import Session

class TestUsersRepo:            
    def test_insert(self, session: Session):
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
    
    def test_update(self, session: Session):
        """Test updating the values of a record.
        Note, for Users repository, since the table only has the generated surrogate primary key and
        the platform id, I don't think testing the repo for update is necessary.

        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        pass
        
    def test_delete(self, session: Session):
        test_id = "ytb_kontio_yahoo_420"
        repo = UserRepository(session=session)
        user = Users(platform_user_id=test_id)
        
        saved_user = repo.insert(user)
        session.flush()
        session.commit()
        
        conditions = dict()
        conditions["platform_user_id"] = test_id
        repo.delete(conditions=conditions)
        session.flush()
        
        fetched_results = repo.get_by(platform_user_id=test_id)
        assert len(fetched_results) == 0 # Check that the user is deleted.        
    
    def test_ensure_users_exist(self, session):
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
        

class TestVideoRepo:
    def test_insert(self, session: Session):
        """Test inserting a video into the repository

        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        repo = VideoRepository(session=session)
        time = datetime.now(timezone.utc)
        video = Videos(
            platform_video_id="ytb_873rc3",
            title="Totally not fake, this person refuses the batchall!",
            view_count=80000,
            comment_count=100,
            is_livestream=False,
            published_at=time,
        )
        
        saved = repo.insert(video)
        session.flush()
        assert saved.id is not None  # UUIDv7 generated!
        fetched = repo.get_by(platform_video_id="ytb_873rc3")
        
        assert len(fetched) == 1
        assert fetched[0].title == "Totally not fake, this person refuses the batchall!"
        assert fetched[0].view_count == 80000
        assert fetched[0].comment_count == 100
        assert fetched[0].is_livestream is False
        assert fetched[0].published_at == time
        
        # NOTE: This is just testing the database, for the extractor pipeline into the database, we will test whether the owner
        #       of the video also appears in the corresponding Users table.
    
    def test_update(self, session: Session):
        """
        Test updating fields on an existing video.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        repo = VideoRepository(session=session)
        video = Videos(
            platform_video_id="ytb_vid_002", 
            title="Original Title", 
            view_count=100,
        )
        video_1 = Videos (
            platform_video_id="ytb_vid_003",
            title="Foo Bar",
            view_count=900,
        )
        repo.insert(video)
        repo.insert(video_1)
        session.flush()
        # Update view_count and title + a new value for a previously null column
        updated_time = datetime.now(timezone.utc)
        rows_affected = repo.update(
            values={"title": "Updated Title", "view_count": 9999, "published_at": updated_time},
            conditions={"platform_video_id": "ytb_vid_002"},
        )
        session.flush()
        assert rows_affected == 1
        updated = repo.get_by(platform_video_id="ytb_vid_002")[0]
        assert updated.title == "Updated Title"
        assert updated.view_count == 9999
        assert updated.published_at == updated_time
    
    def test_delete(self, session: Session):
        """
        Test deleting a video by condition.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        repo = VideoRepository(session=session)
        video = Videos(platform_video_id="ytb_vid_003", title="To Be Deleted")
        repo.insert(video)
        session.flush()
        # Delete it
        rows_affected = repo.delete(conditions={"platform_video_id": "ytb_vid_003"})
        session.flush()
        assert rows_affected == 1
        assert len(repo.get_by(platform_video_id="ytb_vid_003")) == 0
    
    def test_insert_or_update(self, session: Session):
        """
        Test the pipeline helper: creates if new, updates stats if already exists.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        repo = VideoRepository(session=session)
        initial_data = {
            "platform_video_id": "ytb_vid_004",
            "title": "Sanguinius is back?!? NOT FAKE, TOTALLY REAL",
            "view_count": 4200000,
            "comment_count": 112322,
            "is_livestream": True,
        }
        # Create the video
        video_1 = repo.insert_or_update(initial_data)
        assert video_1.id is not None
        assert video_1.title == "Sanguinius is back?!? NOT FAKE, TOTALLY REAL"
        assert video_1.view_count == 4200000
        assert video_1.comment_count == 112322
        assert video_1.is_livestream is True
        
        original_uuid = video_1.id
        # Re-scraping the same video with updated view counts
        updated_data = {
            "platform_video_id": "ytb_vid_004",
            "view_count": 5200000,     # Views went up!
            "comment_count": 120322,    # Comments went up!
        }
        video_2 = repo.insert_or_update(updated_data)
        # The method should NOT create a new row; it should retain the same UUID as well as the updated stats!
        assert video_2.id == original_uuid
        assert video_2.view_count == 5200000
        assert video_2.comment_count == 120322
        # Verify that only 1 video record exists in the database
        all_videos = repo.get_by(platform_video_id="ytb_vid_004")
        assert len(all_videos) == 1

class TestCommentRepo:
    def test_insert(self, session: Session):
        pass

    def test_update(self, session: Session):
        pass
    
    def test_delete(self, session: Session):
        pass
    
    def test_insert_extracted_batch(self, session: Session):
        pass
    
class TestLiveChatRepo:
    def test_insert(self, session: Session):
        pass

    def test_update(self, session: Session):
        pass
    
    def test_delete(self, session: Session):
        pass
    
    def test_insert_extracted_batch(self, session: Session):
        pass