from typing import Dict

from extractor.youtube_extractor import YoutubeExtractor
from src.data.database_manager import DatabaseManager
from src.auth_handler.auth_manager import AuthManager

from src.data.comment_repository import CommentRepository
from src.data.livechat_repository import LivechatRepository
from src.data.user_repository import UserRepository
from src.data.video_repository import VideoRepository


class YoutubeIngestionPipeline:
    """Coordinating data 
    """