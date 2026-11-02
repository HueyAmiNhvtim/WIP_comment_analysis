from sqlalchemy.orm import Session

from src.data.base_repository import BaseRepository
from typing import List, Dict

from src.data.models import Videos

from sqlalchemy import select, update, delete


class VideoRepository(BaseRepository[Videos]):
    def __init__(self, session: Session):
        super().__init__(session)
    
    def get_by(self, n: int=1, offset: int=0, **kwargs) -> List[Videos]:
        if n == -1:
            return self.get_by_all(**kwargs)
        
        stmt = select(Videos).filter_by(**kwargs)
        if offset > 0:
            stmt = stmt.offset(offset=offset)
        if n >= 1:
            stmt = stmt.limit(limit=n)
        # scalars are used instead of execute so that we receive the list of 
        # ORM Python objects rather than list of tuples of values of rows from the table
        return list(self.session.scalars(stmt).all())
    
    def get_by_all(self, **kwargs) -> List[Videos]:
        stmt = select(Videos).filter_by(**kwargs)
        return list(self.session.scalars(stmt).all())
    
    def insert(self, entity: Videos) -> Videos:
        self.session.add(entity)
        return entity
    
    def insert_all(self, entities: List[Videos]) -> List[Videos]:
        self.session.add_all(entities)
        return entities
    
    def update(self, values: Dict, conditions: Dict) -> int:
        stmt = update(Videos).filter_by(**conditions).values(**values)
        result = self.session.execute(stmt)
        return result.rowcount
    
    def delete(self, conditions: Dict) -> int:
        stmt = delete(Videos).filter_by(**conditions)
        result = self.session.execute(stmt)
        return result.rowcount
    
    def insert_or_update(self, video_data: Dict) -> Videos:
        """Inserts a new video, or updates the columns if the videos already exists in the table.
        Useful for when you want to update the video later on.
        Returns:
            Videos: the saved Videos ORM object containing its video.id
        """
        # Kinda feels like this is gonna be the bottleneck...But I have to make this work first.
        # But...we index the video_ids so index-boosted search time is gonna alleviate the supposed bottleneck I think.
        existing = self.get_by(platform_video_id=video_data["platform_video_id"])
        
        if existing:
            video = existing[0] # There can be like one unique instance for every video 
            # Update the columns that can change over time. See base.py in the extractor and models.py for the type of columns
            # that are potentially mutable for videos
            video.view_count = video_data.get(video_data["view_count"], video.view_count)
            video.comment_count = video_data.get(video_data["comment_count"], video.comment_count)
            # Change the thing, SQLAlchemy's dirty cchecking will automatically send the UPDATE equivalent upon flushing it.
        else:
              # Create brand new video with all fields from extractor
            video = Videos(
                platform_video_id=video_data["platform_video_id"],
                title=video_data["title"],
                published_at=video_data.get("published_at"),
                view_count=video_data.get("view_count"),
                comment_count=video_data.get("comment_count"),
                is_livestream=video_data.get("is_livestream", False)
            )
            self.insert(video)
        
        self.session.flush() # Move changes from Python to the database's transactional offer
        return video