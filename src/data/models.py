from sqlalchemy.orm import DeclarativeBase
from typing import List, Optional

from uuid import uuid7
from uuid import UUID as UUIDType
from sqlalchemy import Uuid as UUIDCol

from sqlalchemy import String, Integer, BigInteger, DateTime, Text, Boolean # Text: Variable length VARCHAR
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from sqlalchemy import Table, Column

# Separate the models layer from the repositories to allow separation of responsibilities
# The models describe what the data looks like, while the repositories describes how to perform operataions to get them.
class Base(DeclarativeBase): # This class already contains the MetaData object, basically maps the SQL table to its string name
    pass

# Setting timezone=True will ensure that the timezone-aware stuff that Youtube API (or possibly other platforms' APIs)
# returns will be stored properly inside the database. If we don't enable that, it will be turned into naive time, which
# would cause problem should we do sth like compare the time returned by API and query the comments published within that 
# that result.

class UUIDMixin:
    id: Mapped[UUIDType] = mapped_column(
        UUIDCol(as_uuid=True),  # SQLAlchemy will represents column as python uuid.UUID objects in mem, but store it as Postgre's UUID type in persistent memory
        primary_key=True,
        default=uuid7, # Tells Python to generate a new UUID7 everytime a new instance is created
        nullable=False,
        sort_order=-1000 # Position so low that sqlalchemy will place it as the first column in every table this mixin is part of
    )

# Composite primary keys, right.
video_user_juction_table = Table(
    "videos_users",
    Base.metadata,
    Column("video", ForeignKey("videos.id"), primary_key=True),
    Column("user", ForeignKey("users.id"), primary_key=True)
)

class Videos(Base, UUIDMixin):
    __tablename__ = "videos"
    platform_video_id: Mapped[str] = mapped_column(String(100), unique=True, index=True) # Youtube's video_id (and probably livestream id) max length is 11 chars, Idk about Twitch's tho, so I'm gonna put 100 just in case.
    title: Mapped[str] = mapped_column(String(140), nullable=False)  # Youtube video title limit is 100 characters. Twitch's is 140. That's good. Free constraint! 
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # So you don't have to include the type name inside mapped_column
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    is_livestream: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    # back_populates are for synchronizing Python states of the table without having to reload the database.
    # cascade: Basically force comments to follow videos wherever it go, including to the trash bin.
    comments: Mapped[List["Comments"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    livechats: Mapped[List["LiveComments"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    users: Mapped[List["Users"]] = relationship(secondary=video_user_juction_table, back_populates="videos")

# Why separate comments and livecomments? I think it's for the fact that if we want to collect additional data specific to livechats
# (ex: Livechats that donates money for example), we can just alter the livecomments table rather than updating the entire combined
# comment + livechat table (which could be quite big)    
class Comments(Base, UUIDMixin):
    __tablename__ = "comments"
    platform_comment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)        
    text: Mapped[str] = mapped_column(Text, insert_default="")
    
    # Video - Comments: 1-many. User - comment: 1-many
    user_id = mapped_column(ForeignKey("users.id"), nullable=False)    # No, deleted users will remove their comments too, at least for Youtube
    video_id = mapped_column(ForeignKey("videos.id"), nullable=False) # No way for videos tho, if videos are deleted, how do you extract their comments? 
    
    # Relationships
    video: Mapped["Videos"] = relationship(back_populates="comments")
    user: Mapped["Users"] = relationship(back_populates="comments")
    
class LiveComments(Base, UUIDMixin):
    __tablename__ = "livecomments"
    platform_comment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)       
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Maybe the API will provide us with the actual time (or that chat_extracter_thing)         
    text: Mapped[str] = mapped_column(Text, insert_default="")
    
    # Video - Comments: 1-many. User - comment: 1-many
    user_id = mapped_column(ForeignKey("users.id")) # Same rationale as shown in Comments
    video_id = mapped_column(ForeignKey("videos.id"))
    
    # Relationships
    video: Mapped["Videos"] = relationship(back_populates="livechats")
    user: Mapped["Users"] = relationship(back_populates="livechats")
    
                                  
class Users(Base, UUIDMixin): 
    __tablename__ = "users"
    platform_user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Relationships
    comments: Mapped[List["Comments"]] = relationship(back_populates="user")
    livechats: Mapped[List["LiveComments"]]= relationship(back_populates="user")
    videos: Mapped[List["Videos"]] = relationship(secondary=video_user_juction_table, back_populates="users")

# Nah, we're not going to store user names for privacy sake.