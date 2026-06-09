from beanie import Document
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import Field

class CommunityPost(Document):
    userEmail: str
    userName: str
    content: str
    mediaUrl: Optional[str] = None
    mediaType: Optional[str] = None # image, video
    tags: List[str] = [] # bodybuilding, trainer, etc
    likes: list[str] = [] # list of user emails
    comments: list[dict] = [] # {id, userEmail, userName, text, timestamp, parentId}
    views: int = 0
    viewers: List[str] = [] # list of unique user emails who viewed
    isAnnouncement: bool = False
    reports: List[str] = [] # User emails who reported
    isArchived: bool = False
    taggedUsers: List[str] = [] # List of user emails tagged in this post
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "community_posts"

class CommunityChat(Document):
    userEmail: str
    userName: str
    message: str
    mediaUrl: Optional[str] = None
    mediaType: Optional[str] = None # image, video, audio
    isUnsent: bool = False
    deletedFor: List[str] = [] # list of user emails who deleted this for themselves
    clientMsgId: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "community_chats"

class PrivateMessage(Document):
    senderEmail: str
    receiverEmail: str
    message: str
    mediaUrl: Optional[str] = None
    mediaType: Optional[str] = None # image, video, audio
    isRead: bool = False
    isUnsent: bool = False
    deletedFor: List[str] = [] # list of user emails who deleted this for themselves
    clientMsgId: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "private_messages"

class SocialLink(Document):
    senderEmail: str
    receiverEmail: str
    status: str = "pending" # pending, accepted, ignored
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "social_links"

class Story(Document):
    userEmail: str
    userName: str
    mediaUrl: str
    mediaType: str # image, video
    likes: List[str] = [] # User emails who liked this story
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiresAt: datetime

    class Settings:
        name = "community_stories"

class SocialProfile(Document):
    userEmail: str
    handle: str
    bio: Optional[str] = ""
    fitnessGoals: Optional[str] = ""
    transformations: List[str] = [] # List of media URLs
    badges: List[str] = [] # ["strength_master", "early_adopter"]
    interests: Dict[str, float] = {} # bodybuilding: 5.0, etc
    followers: List[str] = [] # Emails
    following: List[str] = [] # Emails
    postsCount: int = 0
    views30Days: int = 0
    isVerified: bool = False
    isInitialized: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "social_profiles"

class CommunityForumTopic(Document):
    userEmail: str
    userName: str
    category: str # "Tips", "Success Stories", "Q&A"
    title: str
    content: str
    mediaFiles: List[dict] = [] # list of {url, type}
    replies: List[dict] = [] # {id, userEmail, userName, text, timestamp}
    views: int = 0
    likes: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "community_forums"

class CommunityEvent(Document):
    title: str
    description: str
    date: datetime
    location: str
    type: str # "Workshop", "Group Class", "Social"
    rsvps: List[str] = [] # List of user emails who RSVP'd
    maxAttendees: Optional[int] = None
    createdBy: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "community_events"

class MemberSpotlight(Document):
    userEmail: str
    userName: str
    bio: str
    transformationImage: str
    achievement: str
    activeFrom: datetime
    activeUntil: datetime
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "community_spotlights"
