from app.models.user import User
from app.models.news import NewsItem
from app.models.job import JobListing
from app.models.resource import Resource
from app.models.roadmap import Roadmap, RoadmapNode, UserProgress
from app.models.node_resource import NodeResource
from app.models.community import Post, Comment, PostVote, CommentVote

# Expose them for easy importing like `from app.models import User`
__all__ = [
    'User', 'NewsItem', 'JobListing', 'Resource', 
    'Roadmap', 'RoadmapNode', 'UserProgress', 'NodeResource',
    'Post', 'Comment', 'PostVote', 'CommentVote'
]
