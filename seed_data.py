from app import create_app
from app.extensions import db
from app.models.roadmap import Roadmap, RoadmapNode
from app.models.community import Post, Comment
from app.models.resource import Resource
from app.models.user import User

app = create_app()

with app.app_context():
    print("Seeding dummy data for Roadmaps, Forums, and Resources...")
    
    # Needs a dummy user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@CoreStack.io')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

    # 1. Roadmaps Seed
    if not Roadmap.query.first():
        rm_backend = Roadmap(title="Backend Developer 2026", description="Mastering APIs, Databases, and System Design.")
        rm_ai = Roadmap(title="AI & Machine Learning Engineer", description="From Math fundamentals to LLM deployment.")
        db.session.add_all([rm_backend, rm_ai])
        db.session.commit()
        
        # Nodes for Backend
        db.session.add(RoadmapNode(roadmap_id=rm_backend.id, title="Internet Networking Fundamentals", order_index=1))
        db.session.add(RoadmapNode(roadmap_id=rm_backend.id, title="Relational Databases (PostgreSQL)", order_index=2))
        db.session.add(RoadmapNode(roadmap_id=rm_backend.id, title="System Design & Architecture", order_index=3))
        
        # Nodes for AI
        db.session.add(RoadmapNode(roadmap_id=rm_ai.id, title="Linear Algebra & Calculus", order_index=1))
        db.session.add(RoadmapNode(roadmap_id=rm_ai.id, title="PyTorch & Neural Networks", order_index=2))
        db.session.commit()

    # 2. Forum Seed
    if not Post.query.first():
        p1 = Post(title="Has anyone tried deploying on Fly.io?", content="Looking for architectural advice migrating from AWS to Fly for Postgres.", author_id=admin.id, score=45)
        p2 = Post(title="Show HN: CoreStack is live", content="Just dropped a massive portal. Thoughts?", author_id=admin.id, score=120)
        db.session.add_all([p1, p2])
        db.session.commit()
        
        db.session.add(Comment(body="Fly is great for edge deployments. Just watch out for network partition splits.", post_id=p1.id, author_id=admin.id, score=12))

    # 3. Resources Seed
    if not Resource.query.first():
        r1 = Resource(title="Hussein Nasser: Database Engineering", url="https://www.youtube.com/@husseinnasser", resource_type="YouTube", tags="database,architecture", added_by=admin.id)
        r2 = Resource(title="ByteByteGo System Design", url="https://bytebytego.com/", resource_type="Course", tags="system design", added_by=admin.id)
        db.session.add_all([r1, r2])
        db.session.commit()

    print("Seeding Complete!")
