import os

from redis import Redis
from rq import Queue, Worker

from db import init_db

REDIS_URL = os.environ["REDIS_URL"]


if __name__ == "__main__":
    init_db()
    connection = Redis.from_url(REDIS_URL)
    worker = Worker([Queue("default", connection=connection)], connection=connection)
    worker.work(with_scheduler=True)
