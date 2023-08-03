from pytz import utc

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from settings import DB_URL


jobstores = {
    'postgres': SQLAlchemyJobStore(url=DB_URL)
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    timezone=utc
)
