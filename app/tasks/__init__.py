from app.tasks.fetch_news import fetch_and_store_news
from app.tasks.fetch_jobs import fetch_and_store_jobs

def init_scheduler(scheduler, app):
    """
    Register background jobs.
    Both tasks receive the Flask `app` instance directly so they can push an
    app context WITHOUT calling create_app() again (which would restart the
    scheduler and block Gunicorn workers).
    """
    scheduler.add_job(
        id='fetch_news_task',
        func=fetch_and_store_news,
        args=[app],               # <-- pass the live app object
        trigger='interval',
        seconds=30,
        max_instances=1,          # prevent pileup if a run takes too long
        coalesce=True,
        next_run_time=__import__('datetime').datetime.utcnow()  # run immediately at startup
    )

    scheduler.add_job(
        id='fetch_jobs_task',
        func=fetch_and_store_jobs,
        args=[app],
        trigger='interval',
        minutes=30,
        max_instances=1,
        coalesce=True,
        next_run_time=__import__('datetime').datetime.utcnow()  # run immediately at startup
    )
