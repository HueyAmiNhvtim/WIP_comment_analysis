from sqlalchemy.orm import Session

from src.data.base_repository import BaseRepository
from typing import List, Dict
from uuid import UUID as UUIDType

from src.data.models import Users

from sqlalchemy import select, update, delete

# I don't think we need func here for aggregate functions tbh, feels like that would make the repo do too much.
# Should be reserved for when we doing actual analytics stuff.
# Maybe...just maybe we could incorporate them for some of the simpler aggregate usecases, but I still think that would make the 
# repo do too much.

class UserRepository(BaseRepository[Users]):
    def __init__(self, session: Session):
        super().__init__(session)
    
    def get_by(self, n: int=1, offset: int=0, **kwargs) -> List[Users]:
        if n == -1:
            return self.get_by_all(**kwargs)
        
        stmt = select(Users).filter_by(**kwargs)
        if offset > 0:
            stmt = stmt.offset(offset=offset)
        if n >= 1:
            stmt = stmt.limit(limit=n)
        # scalars are used instead of execute so that we receive the list of User objects rather than list of tuples of values of rows from users
        # select(Users) basically select every single columns from Users
        return list(self.session.scalars(stmt).all())
    
    def get_by_all(self, **kwargs) -> List[Users]:
        stmt = select(Users).filter_by(**kwargs)
        return list(self.session.scalars(stmt).all())
    
    def insert(self, entity: Users) -> Users:
        self.session.add(entity)
        return entity
    
    def insert_all(self, entities: List[Users]) -> List[Users]:
        self.session.add_all(entities)
        return entities
    
    def update(self, values: Dict, conditions: Dict) -> int:
        stmt = update(Users).filter_by(**conditions).values(**values)
        result = self.session.execute(stmt)
        return result.rowcount
    
    def delete(self, conditions: Dict) -> int:
        stmt = delete(Users).filter_by(**conditions)
        result = self.session.execute(stmt)
        return result.rowcount
    
    def ensure_users_exist(self, platform_user_ids: List[str]) -> Dict[str, UUIDType]:
        """
        Takes a list of platform user id
        and returns a mapping of user ids associated with their internal uuid primary key in the database!
        This function exists because when calling the platform API, they return the IDs associated with the user,
        but in this database, each user record has its primary key of being an internal UUID!
        """
        if not platform_user_ids:
            return {}
        unique_uids = list(set(platform_user_ids))
        # Fetch existing users
        stmt = select(Users).where(Users.platform_user_id.in_(unique_uids))
        existing_users = list(self.session.scalars(stmt).all())
        user_map = {u.platform_user_id: u.id for u in existing_users}
        # Create new users that haven't appeared in the database!
        new_users = [
            Users(platform_user_id=uid)
            for uid in unique_uids
            if uid not in user_map
        ]
        if new_users:
            self.session.add_all(new_users)
            self.session.flush()  # Put the insertion of new users into the database's existing transaction!
                                  # No using commit() because in case of crashing after running this method,
                                  # you can get a bunch of orphaned users with null foreign keys
            for u in new_users:
                user_map[u.platform_user_id] = u.id # By flushing, Postgre will generate the IDs for the new users, so those entries can be added to the user map. 
        return user_map