from typing import Dict

from src.extractor.base_extractor import BaseExtractor
from src.extractor.youtube_extractor import YoutubeExtractor

from src.data.database_manager import DatabaseManager
from src.auth_handler.auth_manager import AuthManager

from src.data.comment_repository import CommentRepository
from src.data.livechat_repository import LivechatRepository
from src.data.user_repository import UserRepository
from src.data.video_repository import VideoRepository


class Initialize:
    """Initializing the database manager and the extractor classes
    """
    def __init__(self, env_path: str) -> None:
        self.env_path = env_path
    
    def initialize_database(self) -> DatabaseManager:
        return DatabaseManager(env_path=self.env_path)
    
    def initialize_extractors(self) -> Dict[str, BaseExtractor]:
        auth = AuthManager(env_path=self.env_path)
        return {
            # Add other platforms here too.
            "youtube": YoutubeExtractor(youtube_client=auth.authenticate_youtube())
        }

class IngestionPipeline:
    """
    Coordinating data extraction from a platform and 
    persisting it atomically into the database
    """    
    def __init__(self, db_manager: DatabaseManager, extractor: BaseExtractor) -> None:
        self.db_manager = db_manager
        self.extractor = extractor
    
    def ingest(self, video_id: str) -> Dict[str, int]:
        """Extract necessary data (for the purpose of this project) from video_id

        Args:
            video_id (str): id of the video

        Returns:
            Dict[str, int]: How much data have been extracted
        """
        result = {"updated_users_total": 0, "new_comments": 0, "new_livechats": 0}
        # Extract the video
        extracted_data = self.extractor.extract_everything(video_id=video_id)
        video_data = extracted_data.get("video", {})
        
        if not video_data:
            return result
        
        # Load the video into the database (Single atomic Unit-of-work transaction)
        with self.db_manager.session_scope() as session:
            user_repo = UserRepository(session)
            video_repo = VideoRepository(session)
            comment_repo = CommentRepository(session)
            livechat_repo = LivechatRepository(session)
            # Ensure all users exist and get {platform_user_id: internal_uuid}
            user_map = user_repo.ensure_users_exist(platform_user_ids=extracted_data["users"])
            # Insert or update video (and automatically link video.users in videos_users junction table)
            video = video_repo.insert_or_update(video_data=video_data)            
            
            # Batch insert comments and livechats
            new_comments = comment_repo.insert_extracted_batch(
                raw_comments=extracted_data["comments"],
                video_id=video.id,
                user_map=user_map
            )
            new_livechats = livechat_repo.insert_extracted_batch(
                raw_comments=extracted_data["comments"],
                video_id=video.id,
                user_map=user_map 
            )
            
            result["updated_users_total"] = len(user_map)
            result["new_comments"] = len(new_comments)
            result["new_livechats"] = len(new_livechats)
        
        return result