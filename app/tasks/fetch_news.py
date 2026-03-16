import feedparser
import requests
from datetime import datetime
from time import mktime

# ─── RSS feeds to poll ────────────────────────────────────────────────────────
RSS_FEEDS = [
    {'url': 'https://news.ycombinator.com/rss',              'source': 'HackerNews'},
    {'url': 'https://techcrunch.com/feed/',                   'source': 'TechCrunch'},
    {'url': 'https://dev.to/feed',                            'source': 'Dev.to'},
    {'url': 'https://www.theverge.com/tech/rss/index.xml',    'source': 'The Verge'},
    {'url': 'https://feeds.arstechnica.com/arstechnica/index','source': 'Ars Technica'},
    {'url': 'https://www.wired.com/feed/rss',                 'source': 'Wired'},
    {'url': 'https://thenextweb.com/feed',                    'source': 'The Next Web'},
    {'url': 'https://engineering.fb.com/feed/',               'source': 'Meta Engineering'},
    {'url': 'https://github.blog/feed/',                      'source': 'GitHub Blog'},
    {'url': 'https://stackoverflow.blog/feed/',               'source': 'StackOverflow Blog'},
    {'url': 'https://www.infoq.com/feed',                     'source': 'InfoQ'},
    {'url': 'https://feeds.feedburner.com/TheHackersNews',    'source': 'Hacker News Security'},
    {'url': 'https://lobste.rs/rss',                          'source': 'Lobsters'},
]

def fetch_and_store_news(app):
    """
    Called by APScheduler — receives the *already created* Flask app instance
    so it can push an app context safely without re-running the factory.
    """
    from app.extensions import db
    from app.models.news import NewsItem

    with app.app_context():
        ts = datetime.utcnow().strftime('%H:%M:%S')
        print(f"[{ts} UTC] APScheduler: fetch_and_store_news() START")

        new_count = 0
        for feed_data in RSS_FEEDS:
            try:
                parsed = feedparser.parse(
                    feed_data['url'],
                    agent='CoreStack/1.0 (+https://github.com/CoreStack)'
                )
                for entry in parsed.entries[:8]:
                    url = getattr(entry, 'link', None)
                    if not url:
                        continue
                    # Skip if we already stored this URL
                    if NewsItem.query.filter_by(url=url).first():
                        continue

                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub = datetime.fromtimestamp(mktime(entry.published_parsed))
                    else:
                        pub = datetime.utcnow()

                    db.session.add(NewsItem(
                        title    = entry.get('title', 'Untitled')[:255],
                        url      = url,
                        source   = feed_data['source'],
                        published_at = pub,
                        summary  = entry.get('summary', '')[:1000]
                    ))
                    new_count += 1

                db.session.commit()

            except Exception as exc:
                db.session.rollback()
                print(f"  [WARN] {feed_data['source']}: {exc}")

        ts2 = datetime.utcnow().strftime('%H:%M:%S')
        print(f"[{ts2} UTC] APScheduler: fetch_and_store_news() DONE — {new_count} new articles")
