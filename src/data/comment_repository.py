from src.data.base_repository import BaseRepository
from src.data.models import Comments
from typing import List, Dict
from uuid import UUID as UUIDType

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete


class CommentRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session)
    
    def get_by(self, n: int=1, offset: int=0, **kwargs) -> List[Comments]:
        if n == -1:
            return self.get_by_all(**kwargs)
        
        stmt = select(Comments).filter_by(**kwargs)
        if offset > 0:
            stmt = stmt.offset(offset=offset)
        if n >= 1:
            stmt = stmt.limit(limit=n)
        # scalars are used instead of execute so that we receive the list of 
        # ORM Python objects rather than list of tuples of values of rows from the table
        return list(self.session.scalars(stmt).all())

    def get_by_all(self, **kwargs) -> List[Comments]:
        stmt = select(Comments).filter_by(**kwargs)
        return list(self.session.scalars(stmt).all())
    
    def insert(self, entity: Comments):
        self.session.add(entity)
        return entity
    
    def insert_all(self, entities: List[Comments]) -> List[Comments]:
        self.session.add_all(entities)
        return entities
    
    def update(self, values: Dict, conditions: Dict) -> int:
        stmt = update(Comments).filter_by(**conditions).values(**values)
        result = self.session.execute(stmt)
        return result.rowcount
    
    def delete(self, conditions: Dict) -> int:
        stmt = delete(Comments).filter_by(**conditions)
        result = self.session.execute(stmt)
        return result.rowcount
    
    def insert_extracted_batch(self, raw_comments: List[Dict], video_id: UUIDType, user_map: Dict[str, UUIDType]) -> List[Comments]:
        """
        Filters out already-saved comments and inserts only the new ones.
        Useful for when the thing rescrape the same video's comment sections.
        Note that user_map is a dictionary mapping user's platform id to their internal UUID
        """
        if not raw_comments:
            return []
        # Find which comments already exist in Postgres for this batch
        incoming_ids = [c["platform_comment_id"] for c in raw_comments]
        stmt = select(Comments.platform_comment_id).where(Comments.platform_comment_id.in_(incoming_ids))
        existing_ids = set(self.session.scalars(stmt).all())
        # Build model instances ONLY for truly new comments
        new_comments = [
            Comments(
                platform_comment_id=c["platform_comment_id"],
                video_id=video_id,
                user_id=user_map.get(c["platform_user_id"]),
                text=c["text"],
                published_at=c.get("published_at")
            )
            for c in raw_comments
            if c["platform_comment_id"] not in existing_ids
        ]
        # Batch insert the new comments
        if new_comments:
            self.insert_all(new_comments)
        return new_comments