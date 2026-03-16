from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from sqlalchemy import desc

from app.extensions import db, socketio
from app.models.news import NewsItem
from app.models.job import JobListing
from app.models.roadmap import Roadmap, RoadmapNode, UserProgress
from app.models.resource import Resource
from app.models.community import Post, Comment, PostVote, CommentVote, Subreddit, SubredditMember
from app.models.user import User

from app.forms.auth import LoginForm, RegistrationForm

# Create a single Catch-All Blueprint for the entire app
bp = Blueprint('views', __name__)

# ==========================================
# MAIN ROUTING
# ==========================================

def get_diverse_news(limit=15):
    """Round-robin across sources so no single feed dominates."""
    recent_news = NewsItem.query.order_by(desc(NewsItem.published_at)).limit(100).all()
    source_map = {}
    for item in recent_news:
        source_map.setdefault(item.source, []).append(item)
    diverse_news = []
    while len(diverse_news) < limit and any(source_map.values()):
        for source in list(source_map.keys()):
            if source_map[source]:
                diverse_news.append(source_map[source].pop(0))
            if len(diverse_news) >= limit:
                break
    return diverse_news

def compute_matched_jobs(jobs):
    """Return a dict of {job_id: match_score} for the current logged-in user."""
    if not current_user.is_authenticated:
        return {}
    # Collect all skills from completed nodes
    completed_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    node_ids = [p.node_id for p in completed_progress]
    if not node_ids:
        return {}
    nodes = RoadmapNode.query.filter(RoadmapNode.id.in_(node_ids)).all()
    user_skills = set()
    for node in nodes:
        if node.skills_tags:
            for tag in node.skills_tags.split(','):
                user_skills.add(tag.strip().lower())
    # Score each job
    matched = {}
    for job in jobs:
        if job.required_skills:
            job_skills = {s.strip().lower() for s in job.required_skills.split(',')}
            score = len(user_skills & job_skills)
            if score > 0:
                matched[job.id] = score
    return matched

@bp.route('/')
def index():
    latest_news = get_diverse_news(15)
    all_jobs    = JobListing.query.filter_by(is_active=True).order_by(desc(JobListing.posted_at)).limit(24).all()
    roadmaps    = Roadmap.query.all()
    resources   = Resource.query.order_by(desc(Resource.created_at)).limit(12).all()

    # ── FORUM INTEGRATION ──
    posts       = Post.query.order_by(desc(Post.created_at)).limit(4).all()

    matched_jobs = compute_matched_jobs(all_jobs)
    # Sort: matched jobs first (by score desc), then the rest
    latest_jobs = sorted(all_jobs, key=lambda j: matched_jobs.get(j.id, 0), reverse=True)[:12]

    return render_template('index.html', news=latest_news, jobs=latest_jobs,
                           roadmaps=roadmaps, resources=resources,
                           matched_jobs=matched_jobs, posts=posts)


@bp.route('/api/feed')
def api_feed():
    """Polled every 30 s by frontend JS — returns latest diverse news."""
    news = get_diverse_news(15)
    return jsonify(news=[{
        'title':        n.title,
        'url':          n.url,
        'source':       n.source,
        'published_at': n.published_at.strftime('%b %d, %Y')
    } for n in news])



# ==========================================
# AUTH ROUTING
# ==========================================

@bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered engineer! Please log in.', 'success')
        return redirect(url_for('views.login'))
        
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('views.login'))
            
        login_user(user, remember=form.remember_me.data)
        
        # Handle safe redirects
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('views.index')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Log In', form=form)

@bp.route('/auth/logout')
def logout():
    logout_user()
    return redirect(url_for('views.index'))

# ==========================================
# COMMUNITY ROUTING
# ==========================================

@bp.route('/community/')
def community_index():
    sort = request.args.get('sort', 'hot')  # hot | new | top
    posts_q = Post.query
    if sort == 'new':
        posts = posts_q.order_by(Post.created_at.desc()).limit(50).all()
    elif sort == 'top':
        posts = posts_q.order_by(Post.score.desc()).limit(50).all()
    else:  # hot
        posts = posts_q.order_by(Post.score.desc(), Post.created_at.desc()).limit(50).all()
        posts = sorted(posts, key=lambda p: p.hot_score, reverse=True)

    subreddits = Subreddit.query.order_by(Subreddit.name).all()

    # Per-user membership set
    joined_ids = set()
    if current_user.is_authenticated:
        joined_ids = {m.subreddit_id for m in
                      SubredditMember.query.filter_by(user_id=current_user.id).all()}

    return render_template('community/index.html', posts=posts, subreddits=subreddits,
                           joined_ids=joined_ids, sort=sort)

@bp.route('/community/post/<int:id>', methods=['GET'])
def community_detail(id):
    post = Post.query.get_or_404(id)
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.score.desc(), Comment.created_at.desc()).all()
    return render_template('community/detail.html', post=post, comments=comments)

@bp.route('/community/create', methods=['GET', 'POST'])
@login_required
def community_create_post():
    if request.method == 'POST':
        title        = request.form.get('title')
        content      = request.form.get('content')
        post_type    = request.form.get('post_type', 'discussion')
        code_snippet = request.form.get('code_snippet', '')
        subreddit_id = request.form.get('subreddit_id', type=int)
        flair        = request.form.get('flair', '')
        bounty_val   = request.form.get('bounty', type=int, default=0)

        if not title or not content:
            flash('Title and Content are required.', 'danger')
            return redirect(url_for('views.community_create_post'))
            
        if bounty_val < 0:
            flash('Bounty cannot be negative.', 'danger')
            return redirect(url_for('views.community_create_post'))
            
        current_rep = current_user.reputation or 0
        if bounty_val > current_rep:
            flash(f"You don't have enough Reputation ({current_rep} RP) for a {bounty_val} RP bounty.", 'danger')
            return redirect(url_for('views.community_create_post'))
        
        # Deduct bounty
        if bounty_val > 0:
            current_user.reputation = current_rep - bounty_val
        
        post = Post(
            title=title, content=content,
            author_id=current_user.id,
            post_type=post_type,
            code_snippet=code_snippet if post_type == 'review_request' else None,
            subreddit_id=subreddit_id or None,
            flair=flair or None,
            bounty=bounty_val
        )
        db.session.add(post)
        # +5 RP for creating a post
        current_user.reputation = (current_user.reputation or 0) + 5
        db.session.commit()
        
        # Broadcast socket notification for new post
        try:
            socketio.emit('new_post', {
                'title': post.title,
                'author': current_user.username,
                'subreddit': post.subreddit.name if post.subreddit else 'General',
                'url': url_for('views.community_post_detail', post_id=post.id)
            })
        except Exception as e:
            print(f"Socket emit failed: {e}")

        if bounty_val > 0:
            flash(f'Post created successfully with a {bounty_val} RP Bounty! ✨', 'success')
        else:
            flash('Post created successfully! +5 Reputation earned.', 'success')
        if subreddit_id:
            return redirect(url_for('views.subreddit_detail', slug=post.subreddit.slug))
        return redirect(url_for('views.community_detail', id=post.id))
        
    subreddits = Subreddit.query.order_by(Subreddit.name).all()
    # Pre-select subreddit from query param (e.g., when clicking "Post" from a subreddit page)
    preselect = request.args.get('sub', '')
    return render_template('community/create.html', subreddits=subreddits, preselect=preselect)

@bp.route('/community/post/<int:id>/comment', methods=['POST'])
@login_required
def community_add_comment(id):
    post = Post.query.get_or_404(id)
    body = request.form.get('body')
    if body:
        comment = Comment(body=body, post_id=post.id, author_id=current_user.id)
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted.', 'success')
    return redirect(url_for('views.community_detail', id=post.id))


# ==========================================
# SUBREDDIT ROUTES
# ==========================================

@bp.route('/c/')
def subreddits_list():
    """Browse all communities."""
    subreddits = Subreddit.query.order_by(Subreddit.member_count.desc()  # type: ignore
                                          if False else Subreddit.name).all()
    # Sort by member count in Python since SQLite can't aggregate in ORDER BY
    subreddits = sorted(subreddits, key=lambda s: s.member_count, reverse=True)
    joined_ids = set()
    if current_user.is_authenticated:
        joined_ids = {m.subreddit_id for m in
                      SubredditMember.query.filter_by(user_id=current_user.id).all()}
    return render_template('community/subreddits.html', subreddits=subreddits, joined_ids=joined_ids)


@bp.route('/c/<slug>')
def subreddit_detail(slug):
    """Per-subreddit feed (like r/python)."""
    sub = Subreddit.query.filter_by(slug=slug).first_or_404()
    sort = request.args.get('sort', 'hot')

    posts_q = Post.query.filter_by(subreddit_id=sub.id)
    if sort == 'new':
        posts = posts_q.order_by(Post.created_at.desc()).limit(50).all()
    elif sort == 'top':
        posts = posts_q.order_by(Post.score.desc()).limit(50).all()
    else:  # hot
        posts = posts_q.order_by(Post.score.desc(), Post.created_at.desc()).limit(50).all()
        posts = sorted(posts, key=lambda p: p.hot_score, reverse=True)

    is_member = False
    if current_user.is_authenticated:
        is_member = SubredditMember.query.filter_by(
            user_id=current_user.id, subreddit_id=sub.id).first() is not None

    return render_template('community/subreddit.html', sub=sub, posts=posts,
                           sort=sort, is_member=is_member)


@bp.route('/c/new', methods=['GET', 'POST'])
@login_required
def create_subreddit():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        slug        = request.form.get('slug', '').strip().lower().replace(' ', '-')
        description = request.form.get('description', '').strip()
        icon_emoji  = request.form.get('icon_emoji', '💬').strip()
        color       = request.form.get('color', '#38bdf8').strip()
        if not name or not slug:
            flash('Name and slug are required.', 'danger')
            return redirect(url_for('views.create_subreddit'))
        if Subreddit.query.filter_by(slug=slug).first():
            flash(f'A community with slug "{slug}" already exists.', 'danger')
            return redirect(url_for('views.create_subreddit'))
        sub = Subreddit(name=name, slug=slug, description=description,
                        icon_emoji=icon_emoji, color=color, created_by=current_user.id)
        db.session.add(sub)
        db.session.flush()  # get sub.id before commit
        # Creator automatically joins
        member = SubredditMember(user_id=current_user.id, subreddit_id=sub.id)
        db.session.add(member)
        db.session.commit()
        flash(f'Community c/{slug} created! 🎉', 'success')
        return redirect(url_for('views.subreddit_detail', slug=slug))
    return render_template('community/create_subreddit.html')


@bp.route('/c/<slug>/join', methods=['POST'])
@login_required
def join_subreddit(slug):
    sub = Subreddit.query.filter_by(slug=slug).first_or_404()
    existing = SubredditMember.query.filter_by(
        user_id=current_user.id, subreddit_id=sub.id).first()
    if existing:
        db.session.delete(existing)
        flash(f'Left c/{slug}.', 'info')
    else:
        db.session.add(SubredditMember(user_id=current_user.id, subreddit_id=sub.id))
        flash(f'Joined c/{slug}! Welcome! 🎉', 'success')
    db.session.commit()
    return redirect(request.referrer or url_for('views.subreddit_detail', slug=slug))


# ==========================================
# RESOURCES ROUTING
# ==========================================

@bp.route('/resources/')
def resources_index():
    # Simple list of resources, eventually with filters
    resources_list = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template('resources/index.html', resources=resources_list)

@bp.route('/resources/add', methods=['GET', 'POST'])
@login_required
def resources_add_resource():
    if request.method == 'POST':
        title = request.form.get('title')
        url = request.form.get('url')
        resource_type = request.form.get('type')
        tags = request.form.get('tags')
        
        if not title or not url:
            flash('Title and URL are required.', 'danger')
            return redirect(url_for('views.resources_add_resource'))
            
        r = Resource(title=title, url=url, resource_type=resource_type, tags=tags, added_by=current_user.id)
        try:
            db.session.add(r)
            db.session.commit()
            flash('Resource added to the Hub.', 'success')
            return redirect(url_for('views.resources_index'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding resource. URL may already exist.', 'danger')
            
    return render_template('resources/add.html')

# ==========================================
# ROADMAPS ROUTING
# ==========================================

@bp.route('/roadmaps/')
def roadmaps_index():
    roadmaps = Roadmap.query.all()
    return render_template('roadmaps/index.html', roadmaps=roadmaps)

@bp.route('/roadmaps/<int:id>')
def roadmaps_detail(id):
    roadmap = Roadmap.query.get_or_404(id)
    # Order nodes by their order_index
    nodes = RoadmapNode.query.filter_by(roadmap_id=id).order_by(RoadmapNode.order_index).all()
    
    # Calculate progress if logged in
    completed_node_ids = []
    if current_user.is_authenticated:
        completed_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
        completed_node_ids = [p.node_id for p in completed_progress]
        
    return render_template('roadmaps/detail.html', roadmap=roadmap, nodes=nodes, completed_node_ids=completed_node_ids)

@bp.route('/roadmaps/<int:roadmap_id>/complete/<int:node_id>', methods=['POST'])
@login_required
def roadmaps_complete_node(roadmap_id, node_id):
    # Toggle complete
    progress = UserProgress.query.filter_by(user_id=current_user.id, node_id=node_id).first()
    if progress:
        db.session.delete(progress)
        flash('Node marked as incomplete.', 'info')
    else:
        new_progress = UserProgress(user_id=current_user.id, node_id=node_id)
        db.session.add(new_progress)
        flash('Node completed! Awesome progress.', 'success')
        
    db.session.commit()
    return redirect(url_for('views.roadmaps_detail', id=roadmap_id))


# ==========================================
# REPUTATION & VOTING ROUTES
# ==========================================

@bp.route('/community/post/<int:id>/vote', methods=['POST'])
@login_required
def vote_post(id):
    post = Post.query.get_or_404(id)
    value = int(request.form.get('value', 1))  # 1 upvote, -1 downvote
    existing = PostVote.query.filter_by(user_id=current_user.id, post_id=id).first()
    if existing:
        # Toggle off
        post.score -= existing.value
        if existing.value == 1:
            post.author.reputation = max(0, (post.author.reputation or 0) - 10)
        db.session.delete(existing)
    else:
        vote = PostVote(user_id=current_user.id, post_id=id, value=value)
        post.score += value
        if value == 1:
            post.author.reputation = (post.author.reputation or 0) + 10
        db.session.add(vote)
    db.session.commit()
    return redirect(url_for('views.community_detail', id=id))

@bp.route('/community/comment/<int:id>/vote', methods=['POST'])
@login_required
def vote_comment(id):
    comment = Comment.query.get_or_404(id)
    value = int(request.form.get('value', 1))
    existing = CommentVote.query.filter_by(user_id=current_user.id, comment_id=id).first()
    if existing:
        comment.score -= existing.value
        if existing.value == 1:
            comment.author.reputation = max(0, (comment.author.reputation or 0) - 10)
        db.session.delete(existing)
    else:
        vote = CommentVote(user_id=current_user.id, comment_id=id, value=value)
        comment.score += value
        if value == 1:
            comment.author.reputation = (comment.author.reputation or 0) + 10
        db.session.add(vote)
    db.session.commit()
    return redirect(url_for('views.community_detail', id=comment.post_id))

@bp.route('/community/comment/<int:id>/best', methods=['POST'])
@login_required
def mark_best_answer(id):
    comment = Comment.query.get_or_404(id)
    post = Post.query.get_or_404(comment.post_id)
    # Only the post author can mark a best answer
    if post.author_id != current_user.id:
        flash('Only the post author can mark a best answer.', 'danger')
        return redirect(url_for('views.community_detail', id=post.id))
    # Clear any existing best answers on this post
    for c in post.comments:
        if c.is_best_answer and c.id != id:
            c.is_best_answer = False
    if not comment.is_best_answer:
        comment.is_best_answer = True
        bounty_reward = post.bounty or 0
        total_reward = 50 + bounty_reward
        comment.author.reputation = (comment.author.reputation or 0) + total_reward
        
        msg = f'Best answer marked! @{comment.author.username} earned +50 Reputation.'
        if bounty_reward > 0:
            msg = f'Best answer marked! @{comment.author.username} earned +50 Reputation AND claimed your {bounty_reward} RP Bounty! 🎉'
        flash(msg, 'success')
    else:
        comment.is_best_answer = False
        bounty_reward = post.bounty or 0
        total_reward = 50 + bounty_reward
        comment.author.reputation = max(0, (comment.author.reputation or 0) - total_reward)
        flash('Best answer unmarked.', 'info')
    db.session.commit()
    return redirect(url_for('views.community_detail', id=post.id))


# ==========================================
# ==========================================
# GITHUB & GOOGLE OAUTH ROUTES
# ==========================================

import os
import secrets
import requests as http_req
from flask import current_app as app_ctx
from flask import session

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_AUTHORIZATION_BASE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'

@bp.route('/auth/github')
def github_login():
    client_id = os.environ.get('GITHUB_CLIENT_ID', '')
    if not client_id:
        flash('GitHub OAuth is not configured. Please add GITHUB_CLIENT_ID to .env', 'warning')
        return redirect(url_for('views.login'))
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}&scope=read:user,user:email"
    )
    return redirect(github_auth_url)

@bp.route('/auth/github/callback')
def github_callback():
    code = request.args.get('code')
    if not code:
        flash('GitHub OAuth failed — no code received.', 'danger')
        return redirect(url_for('views.login'))

    client_id = os.environ.get('GITHUB_CLIENT_ID', '')
    client_secret = os.environ.get('GITHUB_CLIENT_SECRET', '')

    # Exchange code for access token
    token_resp = http_req.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={'client_id': client_id, 'client_secret': client_secret, 'code': code}
    )
    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        flash('GitHub OAuth failed — could not get access token.', 'danger')
        return redirect(url_for('views.login'))

    # Fetch GitHub user profile
    gh_user = http_req.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    ).json()

    # Get primary email if email is private
    gh_emails = http_req.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    ).json()
    email = next((e['email'] for e in gh_emails if e.get('primary')), gh_user.get('email', ''))

    github_id = str(gh_user['id'])
    github_username = gh_user.get('login', '')
    github_avatar_url = gh_user.get('avatar_url', '')

    # Find or create the user
    user = User.query.filter_by(github_id=github_id).first()
    if not user:
        # Check if a user with that email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            user.github_id = github_id
            user.github_username = github_username
            user.github_avatar_url = github_avatar_url
        else:
            user = User(
                username=github_username,
                email=email,
                github_id=github_id,
                github_username=github_username,
                github_avatar_url=github_avatar_url
            )
            db.session.add(user)
    db.session.commit()
    login_user(user)
    flash(f'Welcome, @{user.username}! Logged in via GitHub.', 'success')
    return redirect(url_for('views.index'))


@bp.route('/auth/google')
def google_login():
    """Redirect to Google for OAuth."""
    if not GOOGLE_CLIENT_ID:
        flash('Google Login is not configured on the server.', 'warning')
        return redirect(url_for('views.login'))
    
    redirect_uri = url_for('views.google_callback', _external=True)
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    url = (
        f"{GOOGLE_AUTHORIZATION_BASE_URL}?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&response_type=code"
        f"&scope=email profile&state={state}"
    )
    return redirect(url)


@bp.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if state != session.get('oauth_state'):
        flash('Invalid OAuth state.', 'danger')
        return redirect(url_for('views.login'))
        
    if not code:
        flash('Google authorization failed.', 'danger')
        return redirect(url_for('views.login'))
        
    # Exchange code for token
    token_url = GOOGLE_TOKEN_URL
    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('views.google_callback', _external=True)
    }
    
    token_resp = http_req.post(token_url, data=token_data)
    if token_resp.status_code != 200:
        flash('Failed to exchange Google OAuth code.', 'danger')
        return redirect(url_for('views.login'))
        
    access_token = token_resp.json().get('access_token')
    
    # Fetch user info
    user_info_resp = http_req.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()
    
    google_id = str(user_info_resp.get('id', ''))
    email = user_info_resp.get('email', '')
    google_avatar_url = user_info_resp.get('picture', '')
    given_name = user_info_resp.get('given_name', '')
    family_name = user_info_resp.get('family_name', '')
    
    if not google_id or not email:
        flash('Retrieving user info from Google failed.', 'danger')
        return redirect(url_for('views.login'))
        
    # Find or create user
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            # Link to existing account
            user.google_id = google_id
            user.google_avatar_url = google_avatar_url
            # We don't need to add it, just commit the changes
        else:
            # Create new user
            base_username = f"{given_name}{family_name}".lower().replace(" ", "")
            if not base_username:
                base_username = email.split('@')[0]
                
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                google_avatar_url=google_avatar_url
            )
            db.session.add(user)
            
    db.session.commit()
    login_user(user)
    flash(f'Welcome, @{user.username}! Logged in via Google.', 'success')
    return redirect(url_for('views.index'))


# ==========================================
# USER PROFILE ROUTE
# ==========================================

@bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    # Fetch GitHub repos if connected
    github_repos = []
    if user.github_username:
        try:
            resp = http_req.get(
                f'https://api.github.com/users/{user.github_username}/repos',
                params={'sort': 'stars', 'per_page': 6},
                timeout=5
            )
            if resp.status_code == 200:
                github_repos = resp.json()
        except Exception:
            pass
    # Completed roadmap nodes count
    completed_count = UserProgress.query.filter_by(user_id=user.id).count()
    posts_count = Post.query.filter_by(author_id=user.id).count()
    return render_template('profile.html', user=user, github_repos=github_repos,
                           completed_count=completed_count, posts_count=posts_count)

@bp.route('/api/user/<username>/activity')
def user_activity(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    activity_map = {}
    
    # 1. Posts
    posts = Post.query.filter_by(author_id=user.id).all()
    for p in posts:
        date_str = p.created_at.strftime('%Y-%m-%d')
        activity_map[date_str] = activity_map.get(date_str, 0) + 2  # 2 points for a post
        
    # 2. Comments
    comments = Comment.query.filter_by(author_id=user.id).all()
    for c in comments:
        date_str = c.created_at.strftime('%Y-%m-%d')
        activity_map[date_str] = activity_map.get(date_str, 0) + 1  # 1 point for a comment
        
    # 3. Roadmap Progress (Assuming we had completed_at, but we only have user/node association)
    # If UserProgress does not have a timestamp, we skip it. Let's check if UserProgress has a timestamp.
    # We will assume UserProgress has a created_at column or we just skip it if it throws an error in runtime.
    # To be safe, let's look at models, but I can just wrap it in a try-except.
    
    try:
        progress_items = UserProgress.query.filter_by(user_id=user.id).all()
        for prog in progress_items:
            # Check if created_at exists
            if hasattr(prog, 'created_at') and prog.created_at:
                date_str = prog.created_at.strftime('%Y-%m-%d')
                activity_map[date_str] = activity_map.get(date_str, 0) + 3 # 3 points for completing roadmap node
    except Exception:
        pass
        
    # Convert dict to array of objects for easier D3/Heatmap processing
    # format: [ { "date": "2023-10-15", "count": 4 }, ... ]
    data = [{"date": k, "count": v} for k, v in activity_map.items()]
    return jsonify(data)


# ==========================================
# CODE SANDBOX API
# ==========================================

@bp.route('/api/run-code', methods=['POST'])
def run_code():
    """Proxy to the Piston public API for safe sandboxed code execution."""
    data = request.get_json()
    language = data.get('language', 'python')
    code = data.get('code', '')
    version_map = {
        'python': '3.10.0',
        'javascript': '18.15.0',
        'sql': '3.36.0',
    }
    version = version_map.get(language, '*')
    try:
        resp = http_req.post(
            'https://emkc.org/api/v2/piston/execute',
            json={
                'language': language,
                'version': version,
                'files': [{'name': 'main', 'content': code}]
            },
            timeout=10
        )
        result = resp.json()
        run = result.get('run', {})
        return jsonify({
            'output': run.get('stdout', ''),
            'error': run.get('stderr', ''),
            'code': run.get('code', 0)
        })
    except Exception as e:
        return jsonify({'output': '', 'error': f'Execution service unavailable: {str(e)}', 'code': 1}), 503

@bp.route('/mentors')
def mentors_directory():
    mentors = User.query.filter_by(is_mentor=True).all()
    return render_template('community/mentors.html', mentors=mentors)

