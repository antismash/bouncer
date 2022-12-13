"""Core application logic"""
import asyncio
from datetime import datetime

from aiostandalone import StandaloneApplication
from antismash_models.job import AsyncJob as Job
from redis.asyncio import Redis


async def bounce(app: StandaloneApplication):
    """ Bounce jobs from the waitlist to the main queue """
    conf: RunConfig = app['run_conf']
    db: Redis = app['engine']

    while True:
        await process_waitlists(conf, db)
        await asyncio.sleep(conf.interval)  # type: ignore  # mypy doesn't like dynamic slots


async def process_waitlists(conf: "RunConfig", db: Redis):
    """ Process the wait lists """
    waitlists = await db.keys('{}*'.format(conf.prefix))  # type: ignore  # dynamic slot
    for wl in waitlists:
        identifier = wl.split(':')[-1]

        job_id = await db.lindex(wl, -1)
        if not job_id:
            continue

        try:
            job = await Job(db, job_id).fetch()
        except ValueError:
            continue

        # if we can't move the job, we won't commit this change, so this is safe
        queue = job.target_queues.pop()

        count = await count_identifiers_in_queue(conf, db, identifier, queue)
        if count < conf.max_jobs:  # type: ignore  # dynamic slot
            await db.rpoplpush(wl, queue)

            now = datetime.utcnow()
            job.last_changed = now
            job.trace.append(conf.name)  # type: ignore  # dynamic slot
            await job.commit()


async def count_identifiers_in_queue(conf, db, identifier, queue):
    """Count how many jobs in the queue have the given identifier"""
    count = 0
    for job_id in await db.lrange(queue, 0, -1):
        job = Job(db, job_id)
        await job.fetch()
        if job.email == identifier or job.ip_addr == identifier:
            count += 1

    return count


class RunConfig:
    __slots__ = [
        'interval',
        'max_jobs',
        'name',
        'prefix',
    ]

    def __init__(self, **kwargs):
        for arg in self.__slots__:
            setattr(self, arg, kwargs[arg])

    @classmethod
    def from_argparse(cls, args):
        kwargs = {}
        for arg in cls.__slots__:
            kwargs[arg] = args.__getattribute__(arg)

        return cls(**kwargs)
