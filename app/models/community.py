from app.extensions import db
from datetime import datetime

# ── Subreddit (r/python, r/webdev style community) ──────────────────────────

class Subreddit(db.Model):
    __tablename__ = 'subreddits'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False, unique=True)   # "Python Developers"
    slug        = db.Column(db.String(50),  nullable=False, unique=True)   # "python"
    description = db.Column(db.Text, nullable=True)
    icon_emoji  = db.Column(db.String(10),  default='💬')
    color       = db.Column(db.String(20),  default='#38bdf8')             # hex accent
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    posts   = db.relationship('Post', backref='subreddit', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('SubredditMember', backref='subreddit', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def member_count(self):
        return self.members.count()

    def __repr__(self):
        return f'<Subreddit r/{self.slug}>'


class SubredditMember(db.Model):
    __tablename__ = 'subreddit_members'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=False)
    subreddit_id = db.Column(db.Integer, db.ForeignKey('subreddits.id'), nullable=False)
    joined_at    = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('subreddit_memberships', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'subreddit_id', name='_user_subreddit_uc'),)


# ── Post ──────────────────────────────────────────────────────────────────────

class Post(db.Model):
    __tablename__ = 'posts'

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(255), nullable=False)
    content      = db.Column(db.Text,        nullable=False)
    author_id    = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    score        = db.Column(db.Integer,  default=0)
    post_type    = db.Column(db.String(30),  default='discussion')       # "discussion" | "review_request"
    code_snippet = db.Column(db.Text, nullable=True)
    subreddit_id = db.Column(db.Integer, db.ForeignKey('subreddits.id'), nullable=True)
    flair        = db.Column(db.String(50), nullable=True)               # "Help","Showcase","Discussion"
    bounty       = db.Column(db.Integer, default=0)

    author   = db.relationship('User',    backref=db.backref('posts', lazy='dynamic'))
    comments = db.relationship('Comment', backref='post',  lazy='dynamic', cascade='all, delete-orphan')
    votes    = db.relationship('PostVote', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def hot_score(self):
        """Simple hot ranking: upvotes decay over time (Reddit-like)."""
        ups = max(self.score, 0)
        age_hours = max((datetime.utcnow() - self.created_at).total_seconds() / 3600, 1)
        return round(ups / (age_hours ** 1.5), 4)

    def __repr__(self):
        return f'<Post {self.title}>'


# ── Comment ───────────────────────────────────────────────────────────────────

class Comment(db.Model):
    __tablename__ = 'comments'

    id            = db.Column(db.Integer, primary_key=True)
    body          = db.Column(db.Text,    nullable=False)
    post_id       = db.Column(db.Integer, db.ForeignKey('posts.id'),    nullable=False)
    author_id     = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    score         = db.Column(db.Integer,  default=0)
    is_best_answer= db.Column(db.Boolean,  default=False)

    author = db.relationship('User',        backref=db.backref('comments', lazy='dynamic'))
    votes  = db.relationship('CommentVote', backref='comment', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'


# ── Votes ─────────────────────────────────────────────────────────────────────

class PostVote(db.Model):
    __tablename__ = 'post_votes'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    post_id    = db.Column(db.Integer, db.ForeignKey('posts.id'),  nullable=False)
    value      = db.Column(db.Integer, nullable=False)             # 1 upvote / -1 downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='_user_post_vote_uc'),)


class CommentVote(db.Model):
    __tablename__ = 'comment_votes'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    value      = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='_user_comment_vote_uc'),)
