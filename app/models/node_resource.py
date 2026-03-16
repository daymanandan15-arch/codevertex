from app.extensions import db

class NodeResource(db.Model):
    """A free learning resource (video, course, article) linked to one roadmap node."""
    __tablename__ = 'node_resources'

    id       = db.Column(db.Integer, primary_key=True)
    node_id  = db.Column(db.Integer, db.ForeignKey('roadmap_nodes.id', ondelete='CASCADE'), nullable=False)
    title    = db.Column(db.String(255), nullable=False)
    url      = db.Column(db.String(600), nullable=False)
    rtype    = db.Column(db.String(30), default='Video')   # Video | Course | Docs | Article

    node = db.relationship('RoadmapNode', backref=db.backref('resources', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<NodeResource {self.title}>'
