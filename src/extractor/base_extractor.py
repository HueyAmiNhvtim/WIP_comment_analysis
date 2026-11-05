from abc import ABC, abstractmethod
from typing import List

# TODO: Ok, we have to agree upon the data returned by the extractors...so that we could know how to properly insert stuff
# DATA FORMAT RETURNED BY the extractors, CHANGE IF YOU'RE GONNA MODIFY THE EXTRACTORS:

# Tho, in the future....stuff like comments and livechats or users are probably gonna be generator objects instead?
# This is based on the models.py
# {
#   'video': {
#       platform_video_id: 
#       title: 
#       published_at:    datetime object
#       view_count:
#       comment_count:
#       is_livestream:
#       platform_owner_ids: []
#   },
#   'comments': [{
#       platform_comment_id: 
#       published_at:   datetime object
#       text:  
#       platform_user_id:
#   }, {more_dictionary}],
#   'livechats': [{
#       platform_comment_id: 
#       published_at:   datetime object
#       text: 
#       platform_user_id:
#   }, {more_dictionary}],
#   'users': {
#       platform_user_id: []
#   }
# }


class BaseExtractor(ABC):
    """Abstract base class that enforces a common interface for all platform extractors."""
    
    @abstractmethod
    def extract_video_info(self, video_id: str) -> dict:
        """Extract metadata like title, views, and total comment count."""
        pass

    @abstractmethod
    def extract_comments(self, video_id: str) -> List[dict]:
        """Extract post-stream comments."""
        pass

    @abstractmethod
    def extract_livechat(self, video_id: str) -> List[dict]:
        """Extract live chat logs."""
        pass
    
    # Possible TODO: maybe make this thing multithreaded? Feels like premature optimization as of the time of writing tho. 
    # Rationale for NOT making this abstract:
    # Because we have the defined dataset format, that means extract_users can just use the data format returned by the 
    # other extract_comments stuff and pulled them all.
    def extract_users(self, video: dict, livechats: List[dict], comments: List[dict]):
        """Extract users id from the videos (owner(s)), livechats (commenter), and comments (commenter)
        """
        user_ids = set() # Don't want duplicate user_ids (ex: uploader of a video can argue with other commenters under the video's comment section)
        
        if video["platform_owner_ids"]:
            user_ids.update(video["platform_owner_ids"])
        
        for comment in comments:
            if comment.get("platform_user_id", False):
                user_ids.add(comment["platform_user_id"])
        
        for livechat in livechats:
            if livechat.get("platform_user_id", False):
                user_ids.add(livechat["platform_user_id"])

        return list(user_ids)
    
    # There is still the users thing, tho I think it is the responsibility of the extractors to output that
    def extract_everything(self, video_id: str) -> dict:
        info = dict()
        info["video"] = self.extract_video_info(video_id=video_id)
        if info["video"].get("is_livestream", False):
            livechats = self.extract_livechat(video_id=video_id)
            info["livechats"] = livechats
        else:
            info["livechats"] = []
        comments = self.extract_comments(video_id=video_id)
        info["comments"] = comments
        
        info["users"] = self.extract_users(info["video"], info["livechats"], info["comments"])
        return info
        
    
    