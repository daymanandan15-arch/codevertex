from app.extensions import db
from datetime import datetime

class Roadmap(db.Model):
    __tablename__ = 'roadmaps'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    nodes = db.relationship('RoadmapNode', backref='roadmap', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Roadmap {self.title}>'

class RoadmapNode(db.Model):
    __tablename__ = 'roadmap_nodes'

    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmaps.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0)
    # Comma-separated skill tags, e.g. "python,sql,rest-api" (used for job matching)
    skills_tags = db.Column(db.String(300), nullable=True)
    # Code sandbox support
    sandbox_language = db.Column(db.String(30), nullable=True)   # e.g. "python", "javascript"
    sandbox_starter_code = db.Column(db.Text, nullable=True)
    
    # Optional parent for branching paths
    parent_id = db.Column(db.Integer, db.ForeignKey('roadmap_nodes.id'), nullable=True)
    children = db.relationship('RoadmapNode', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f'<RoadmapNode {self.title}>'

class UserProgress(db.Model):
    __tablename__ = 'user_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey('roadmap_nodes.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships for convenience
    user = db.relationship('User', backref=db.backref('progress', lazy='dynamic'))
    node = db.relationship('RoadmapNode')

    # Ensure a user can only complete a node once
    __table_args__ = (db.UniqueConstraint('user_id', 'node_id', name='_user_node_uc'),)

    def __repr__(self):
        return f'<UserProgress User:{self.user_id} Node:{self.node_id}>'
