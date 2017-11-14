"""Core application logic"""
import asyncio
from antismash_models.job import Job


async def bounce(app):
    """Bounce jobs from the waitlist to the main queue"""
    conf = app['run_conf']
    db = app['engine']

    while True:
        waitlists = await db.keys('{}*'.format(conf.prefix))
        for wl in waitlists:
            identifier = wl.split(':')[-1]
            count = await count_identifiers_in_queue(app, identifier)
            if count < conf.max_jobs:
                await db.rpoplpush(wl, conf.queue)

        await asyncio.sleep(conf.interval)


async def count_identifiers_in_queue(app, identifier):
    """Count how many jobs in the queue have the given identifier"""
    conf = app['run_conf']
    db = app['engine']

    count = 0
    for job_id in await db.lrange(conf.queue, 0, -1):
        job = Job(db, job_id)
        await job.fetch()
        if job.email == identifier or job.ip_addr == identifier:
            count += 1

    return count


class RunConfig:
    __slots__ = [
        'interval',
        'max_jobs',
        'prefix',
        'queue'
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
