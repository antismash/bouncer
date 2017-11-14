"""Command line handling"""
import argparse
from aiostandalone import StandaloneApplication
from envparse import Env

from . import __version__
from .core import RunConfig, bounce
from .database import DatabaseConfig, init_db, close_db


def main():
    """Main CLI handling"""
    env = Env(
        # Redis database URI
        BOUNCER_DB=dict(cast=str, default="redis://localhost:6379/0"),
        # Redis queue
        BOUNCER_QUEUE=dict(cast=str, default="jobs:queued"),
        # Prefix for the waitlist
        BOUNCER_WAITLIST_PREFIX=dict(cast=str, default="jobs:waiting:"),
        # Maximum allowed jobs in queue
        BOUNCER_MAXJOBS=dict(cast=int, default=5),
        # Interval to run check in, in seconds
        BOUNCER_INTERVAL=dict(cast=int, default=60),
    )

    parser = argparse.ArgumentParser(description='Allow jobs from a waitlist to enter the main queue')
    parser.add_argument('--database', dest='db',
                        default=env('BOUNCER_DB'),
                        help="URI of the database containing the job queue (default: %(default)s)")
    parser.add_argument('-q', '--queue',
                        default=env('BOUNCER_QUEUE'),
                        help="Name of the main queue to let jobs into (default: %(default)s))")
    parser.add_argument('-p', '--prefix',
                        default=env('BOUNCER_WAITLIST_PREFIX'),
                        help="Prefix of the waitlists (default: %(default)s)")
    parser.add_argument('-m', '--max-jobs',
                        default=env('BOUNCER_MAXJOBS'), type=int,
                        help="Maximum jobs a waitlisted entity can have in the main queue (default: %(default)s)")
    parser.add_argument('-i', '--interval',
                        default=env('BOUNCER_INTERVAL'), type=int,
                        help="Check interval in seconds (default: %(default)s)")
    parser.add_argument('-V', '--version', action='version', version=__version__)

    args = parser.parse_args()

    app = StandaloneApplication()

    db_conf = DatabaseConfig.from_argparse(args)
    app['db_conf'] = db_conf

    run_conf = RunConfig.from_argparse(args)
    app['run_conf'] = run_conf

    app.on_startup.append(init_db)

    app.on_shutdown.append(close_db)

    app.main_task = bounce

    app.run()


if __name__ == "__main__":
    main()
