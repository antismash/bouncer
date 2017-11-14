"""Tests for the core application logic"""

from antismash_models import Job
from argparse import Namespace
import mockaioredis
import pytest

from antismash_bouncer import core

@pytest.fixture
def db():
    return mockaioredis.MockRedis(encoding='utf-8')


@pytest.fixture
def app(db):
    args = Namespace(interval=5, max_jobs=1, prefix='fake:waiting:', queue="fake:queued")
    conf = core.RunConfig.from_argparse(args)
    app = dict(engine=db, run_conf=conf)
    return app


async def setup_fake_jobs(db):
    fake_jobs = [
        Job(db, 'fake01'),
        Job(db, 'fake02'),
        Job(db, 'fake03'),
        Job(db, 'fake04'),
    ]

    fake_jobs[0].email = "alice@example.org"
    fake_jobs[0].ip_addr = '123.123.123.234'
    await fake_jobs[0].commit()

    fake_jobs[1].email = "bob@example.org"
    fake_jobs[1].ip_addr = '123.123.123.234'
    await fake_jobs[1].commit()

    fake_jobs[2].email = "alice@example.org"
    fake_jobs[2].ip_addr = '123.123.123.234'
    await fake_jobs[2].commit()

    fake_jobs[3].email = "chuck@example.org"
    fake_jobs[3].ip_addr = '123.123.123.235'
    await fake_jobs[3].commit()

    return fake_jobs


@pytest.mark.asyncio
async def test_count_identifiers_in_queue(app):
    conf = app['run_conf']
    db = app['engine']

    fake_jobs = await setup_fake_jobs(db)

    for j in fake_jobs:
        await db.lpush(conf.queue, j.job_id)

    assert await core.count_identifiers_in_queue(conf, db, 'alice@example.org') == 2
    assert await core.count_identifiers_in_queue(conf, db, 'bob@example.org') == 1
    assert await core.count_identifiers_in_queue(conf, db, 'chuck@example.org') == 1
    assert await core.count_identifiers_in_queue(conf, db, '123.123.123.234') == 3
    assert await core.count_identifiers_in_queue(conf, db, '123.123.123.235') == 1
    assert await core.count_identifiers_in_queue(conf, db, 'eve@example.org') == 0


@pytest.mark.asyncio
async def test_process_waitlists(app):

    conf = app['run_conf']
    db = app['engine']

    fake_jobs = await setup_fake_jobs(db)
    await db.lpush('fake:waiting:alice@example.org', fake_jobs[0].job_id, fake_jobs[2].job_id)
    await db.lpush('fake:waiting:bob@example.org', fake_jobs[1].job_id)
    await db.lpush('fake:waiting:chuck@example.org', fake_jobs[3].job_id)

    await core.process_waitlists(conf, db)

    assert await core.count_identifiers_in_queue(conf, db, 'alice@example.org') == 1
    assert await core.count_identifiers_in_queue(conf, db, 'bob@example.org') == 1
    assert await core.count_identifiers_in_queue(conf, db, 'chuck@example.org') == 1
