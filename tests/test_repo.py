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
        """Test inserting a comment into the repository

        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations"""
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        comment_repo = CommentRepository(session)
        
        # Create parent User and Video first (to satisfy foreign keys)
        # This should be alright since if user and video repos fail then their associating tests will fail too.
        user = user_repo.insert(Users(platform_user_id="ytb_c324231"))
        video = video_repo.insert(Videos(platform_video_id="ytb_23453", title="Raven spotted despite reported dead on Rubicon"))
        session.flush()
        
        # Insert Comment
        time = datetime.now(timezone.utc)
        comment = Comments(
            platform_comment_id="ytb_12301",
            video_id=video.id,
            user_id=user.id,
            text="Ain't no way that dude's still alive. fake news, he got the handshake.",
            published_at=time,
        )
        saved = comment_repo.insert(comment)
        session.flush()
        assert saved.id is not None  # UUIDv7 generated!
        fetched = comment_repo.get_by(platform_comment_id="ytb_12301")
        assert len(fetched) == 1
        assert fetched[0].text == "Ain't no way that dude's still alive. fake news, he got the handshake."
        assert fetched[0].video_id == video.id
        assert fetched[0].user_id == user.id
        assert fetched[0].published_at == time

    def test_update(self, session: Session):
        """Test updating comment text.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations"""
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        comment_repo = CommentRepository(session)
        
        user = user_repo.insert(Users(platform_user_id="ytb_user_sh22p"))
        video = video_repo.insert(Videos(platform_video_id="ytb_vid_c2", title="Karaoke NIGHT!!!"))
        session.flush()
        comment_repo.insert(
            Comments(
                platform_comment_id="ytb_comm_2",
                video_id=video.id,
                user_id=user.id,
                text="waru ku nai yo ne",
            )
        )
        session.flush()
        rows = comment_repo.update(
            values={"text": "Edited text (\"typo\" fixed)"},
            conditions={"platform_comment_id": "ytb_comm_2"},
        )
        session.flush()
        assert rows == 1
        updated = comment_repo.get_by(platform_comment_id="ytb_comm_2")[0]
        assert updated.platform_comment_id == "ytb_comm_2"
        assert updated.user_id == user.id
        assert updated.video_id == video.id
        assert updated.text == "Edited text (\"typo\" fixed)"
    
    def test_delete(self, session: Session):
        """Test deleting a comment by condition.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations"""
            
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        comment_repo = CommentRepository(session)
        user = user_repo.insert(Users(platform_user_id="ytb_user_c3"))
        video = video_repo.insert(Videos(platform_video_id="ytb_vid_c3", title="Gaming Stream"))
        session.flush()
        comment_repo.insert(
            Comments(
                platform_comment_id="ytb_comm_003",
                video_id=video.id,
                user_id=user.id,
                text="Spam comment to delete",
            )
        )
        session.flush()
        rows = comment_repo.delete(conditions={"platform_comment_id": "ytb_comm_003"})
        session.flush()
        assert rows == 1
        assert len(comment_repo.get_by(platform_comment_id="ytb_comm_003")) == 0
    
    def test_insert_extracted_batch(self, session: Session):
        """Test pipeline batch insert and verifying deduplication on re-scrapes.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        comment_repo = CommentRepository(session)
        
        # Setup parent video & user map
        video = video_repo.insert(Videos(platform_video_id="ytb_vid_2321", title="MadCat too op pls nerf."))
        session.flush()
        user_map = user_repo.ensure_users_exist(["ytb_u_alpha", "ytb_u_beta"])
        raw_comments_first_run = [
            {
                "platform_comment_id": "comm_1",
                "platform_user_id": "ytb_u_alpha",
                "text": "No, you spheroids are just salty our machines are better.",
                "published_at": datetime.now(timezone.utc),
            },
            {
                "platform_comment_id": "comm_2",
                "platform_user_id": "ytb_u_beta",
                "text": "Even with your Timmys you can't even defeat the phone company kekw.",
                "published_at": datetime.now(timezone.utc),
            },
        ]
        # First ingestion: Both should be inserted
        inserted_first = comment_repo.insert_extracted_batch(
            raw_comments=raw_comments_first_run,
            video_id=video.id,
            user_map=user_map,
        )
        session.flush()
        assert len(inserted_first) == 2
        # Second ingestion (Re-scrape scenario):
        # Includes comm_1 (already in DB) + comm_3 (brand new!)
        raw_comments_second_run = [
            {
                "platform_comment_id": "comm_1",  # Existing!
                "platform_user_id": "ytb_u_alpha",
                "text": "No, you spheroids are just salty our machines are better.",
            },
            {
                "platform_comment_id": "comm_2",
                "platform_user_id": "ytb_u_beta",
                "text": "Even with your Timmys you can't even defeat the phone company kekw.",
            },
            {
                "platform_comment_id": "comm_3",  # Brand new!
                "platform_user_id": "ytb_u_alpha",
                "text": "I challenge you to a trial of grievance.",
                "published_at": datetime.now(timezone.utc),
            },
        ]
        inserted_second = comment_repo.insert_extracted_batch(
            raw_comments=raw_comments_second_run,
            video_id=video.id,
            user_map=user_map,
        )
        session.flush()
        # Deduplication check: Check that ONLY the truly new comment was inserted!
        assert len(inserted_second) == 1
        assert inserted_second[0].platform_comment_id == "comm_3"
        # Total in DB for this video should now be 3 (comm_1, comm_2, comm_3)
        total_comments = comment_repo.get_by(video_id=video.id, n=-1)
        assert len(total_comments) == 3

    
class TestLiveChatRepo:
    def test_insert(self, session: Session):
        """Test inserting a live chat replay message.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        livechat_repo = LivechatRepository(session)
        
        user = user_repo.insert(Users(platform_user_id="ytb_chatter_01"))
        video = video_repo.insert(Videos(platform_video_id="ytb_stream_live", title="AC6 PvP Tournament", is_livestream=True))
        session.flush()
        time = datetime.now(timezone.utc)
        chat_msg = LiveComments(
            platform_comment_id="ytb_chat_msg_100",
            video_id=video.id,
            user_id=user.id,
            text="CORAL ABIDE WITH RUBICON",
            published_at=time,
        )
        
        saved = livechat_repo.insert(chat_msg)
        session.flush()
        assert saved.id is not None
        fetched = livechat_repo.get_by(platform_comment_id="ytb_chat_msg_100")
        assert len(fetched) == 1
        assert fetched[0].text == "CORAL ABIDE WITH RUBICON"
        assert fetched[0].video_id == video.id
        assert fetched[0].user_id == user.id
        assert fetched[0].published_at == time
        
    def test_update(self, session: Session):
        """Test updating live chat message text.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        livechat_repo = LivechatRepository(session)
        user = user_repo.insert(Users(platform_user_id="ytb_chatter_02"))
        video = video_repo.insert(Videos(platform_video_id="ytb_stream_live_2", title="Midnight Karaoke"))
        session.flush()
        livechat_repo.insert(
            LiveComments(
                platform_comment_id="ytb_chat_msg_200",
                video_id=video.id,
                user_id=user.id,
                text="Totally Original chat message that comments about the singer's ability in a flattering way.",
            )
        )
        session.flush()
        rows = livechat_repo.update(
            values={"text": "Updated chat message that comments about the singer's ability in a semi-flattering way"},
            conditions={"platform_comment_id": "ytb_chat_msg_200"},
        )
        session.flush()
        assert rows == 1
        updated = livechat_repo.get_by(platform_comment_id="ytb_chat_msg_200")[0]
        assert updated.platform_comment_id == "ytb_chat_msg_200"
        assert updated.user_id == user.id
        assert updated.video_id == video.id
        assert updated.text == "Updated chat message that comments about the singer's ability in a semi-flattering way"
        
    def test_delete(self, session: Session):
        """Test deleting a live chat message.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        livechat_repo = LivechatRepository(session)
        user = user_repo.insert(Users(platform_user_id="ytb_chatter_03"))
        video = video_repo.insert(Videos(platform_video_id="ytb_stream_live_3", title="Stream with spam"))
        session.flush()
        livechat_repo.insert(
            LiveComments(
                platform_comment_id="ytb_chat_msg_300",
                video_id=video.id,
                user_id=user.id,
                text="Deleted by moderator",
            )
        )
        session.flush()
        rows = livechat_repo.delete(conditions={"platform_comment_id": "ytb_chat_msg_300"})
        session.flush()
        assert rows == 1
        assert len(livechat_repo.get_by(platform_comment_id="ytb_chat_msg_300")) == 0
        
    def test_insert_extracted_batch(self, session: Session):
        """Test batch insertion and deduplication for high-volume live chat messages.
        Args:
            session (Session): SQLAlchemy session that handles the Python's side of database operations
        """
        user_repo = UserRepository(session)
        video_repo = VideoRepository(session)
        livechat_repo = LivechatRepository(session)
        video = video_repo.insert(Videos(platform_video_id="ytb_stream_batch", title="Grand Finals", is_livestream=True))
        session.flush()
        user_map = user_repo.ensure_users_exist(["ytb_fan_1", "ytb_fan_2"])
        raw_chat_first = [
            {
                "platform_comment_id": "chat_001",
                "platform_user_id": "ytb_fan_1",
                "text": "UTTERLY MOIST",
                "published_at": datetime.now(timezone.utc),
            },
            {
                "platform_comment_id": "chat_002",
                "platform_user_id": "ytb_fan_2",
                "text": "CLUTCH GOD",
                "published_at": datetime.now(timezone.utc),
            },
        ]
        inserted_first = livechat_repo.insert_extracted_batch(
            raw_comments=raw_chat_first,
            video_id=video.id,
            user_map=user_map,
        )
        session.flush()
        assert len(inserted_first) == 2
        # Second scrape: includes chat_002 (existing) + chat_003 (new message)
        raw_chat_second = [
            {
                "platform_comment_id": "chat_002",
                "platform_user_id": "ytb_fan_2",
                "text": "CLUTCH GOD",
            },
            {
                "platform_comment_id": "chat_003",
                "platform_user_id": "ytb_fan_1",
                "text": "GG WP",
                "published_at": datetime.now(timezone.utc),
            },
        ]
        inserted_second = livechat_repo.insert_extracted_batch(
            raw_comments=raw_chat_second,
            video_id=video.id,
            user_map=user_map,
        )
        session.flush()
        # Deduplication check: ONLY chat_003 inserted!
        assert len(inserted_second) == 1
        assert inserted_second[0].platform_comment_id == "chat_003"
        total_chats = livechat_repo.get_by(video_id=video.id, n=-1)
        assert len(total_chats) == 3