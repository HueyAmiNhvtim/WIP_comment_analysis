from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Dict
from sqlalchemy.orm import Session

T = TypeVar("T")

# Basically, CRUD-style stuff.
# CREATE, READ, UPDATE, DELETE
class BaseRepository(ABC, Generic[T]):
    """Abstract generic base class that enforces a common CRUD interface for all repositories."""

    def __init__(self, session: Session):
        """
        Initializes the repository with an active database session.
        :param session: An active SQLAlchemy Session.
        """
        self.session = session

    @abstractmethod
    def get_by(self, n: int=1, offset: int=0, **kwargs) -> List[T]:
        """
        Retrieves the n number of records that matches the specified information with <offset> initial rows skips
        Default of n is 1. n=-1 will retrieve everything instead regardless of <offset> value
        """
        pass
        
    @abstractmethod
    def get_by_all(self, **kwargs) -> List[T]:
        """
        Retrieves every record that matches the specified information
        """
        pass
    
    # Save is fine, it's just getting the info from the scraper (and future TODO: probably from cache?) and save it into the table
    @abstractmethod
    def insert(self, entity: T) -> T:
        """Saves a new entity and flushes/persists it into the corresponding table"""
        pass
    
    @abstractmethod
    def insert_all(self, entities: List[T]) -> List[T]:
        """Save multiple entities and flushes/persists them into the corresponding table"""
        pass
    
    @abstractmethod
    def update(self, values: Dict, conditions: Dict) -> int:
        """Updates existing entities satisfying conditions with values
           Return number of rows successfully updated
        """
        pass

    @abstractmethod
    def delete(self, conditions: Dict) -> int:
        """Deletes an entity that matches the values specified in conditions. Returns number of rows deleted."""
        pass
    
    def flush(self) -> None:
        """
        Sends all staged SQL operations to the databse within the current transaction.
        Note that this does not make the data fully persist to the database, just make the current changes communicate to the sql database!
        See https://stackoverflow.com/questions/4201455/sqlalchemy-whats-the-difference-between-flush-and-commit
        """
        self.session.flush()