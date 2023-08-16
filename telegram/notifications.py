from pytz import utc

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from settings import DB_URL


scheduler = AsyncIOScheduler(
    # jobstores={
    #     'default': SQLAlchemyJobStore(url=DB_URL),
    # },
    timezone=utc,
    executors={
        "cron": ThreadPoolExecutor()
    },
    job_defaults={
        'coalesce': False,
        'max_instances': 1
    }
)
