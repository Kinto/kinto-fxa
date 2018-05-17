"""
Main entry point for kinto_fxa scripts.
"""

import argparse
import logging
import os

from pyramid.paster import bootstrap

from .process_account_events import process_account_events

DEFAULT_CONFIG_FILE = os.getenv('KINTO_INI', 'config/kinto.ini')
logger = logging.getLogger(__name__)


def main(args=None):
    parser = argparse.ArgumentParser(description="Listen to the queue for account messages.")
    parser.add_argument('--ini', dest='ini_file', required=False, default=DEFAULT_CONFIG_FILE,
                        help="path to kinto INI file")
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='kinto-fxa command to run',
                                       dest='subcommand')
    subparsers.required = True
    subparser = subparsers.add_parser('process-account-events')

    subparser.add_argument('queue_name',
                           help="SQS queue on which to listen for events")
    subparser.add_argument('--aws-region',
                           help="aws region in which the queue can be found")
    subparser.add_argument("--queue-wait-time", type=int, default=20,
                           help="Number of seconds to wait for jobs on the queue")

    opts = parser.parse_args(args)

    logger.debug("Using config file %r", opts.ini_file)
    config = bootstrap(opts.ini_file)

    process_account_events(
        config, opts.queue_name,
        opts.aws_region, opts.queue_wait_time)
    return 0


if __name__ == '__main__':  # pragma: nocover
    main()
