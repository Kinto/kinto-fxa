# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
"""Script to process account-related events from an SQS queue.

This script polls an SQS queue for events indicating activity on an upstream
account, as documented here:

  https://github.com/mozilla/fxa-auth-server/blob/master/docs/service_notifications.md

The following event types are currently supported:

  * "delete": the account was deleted; we delete their default bucket
    to comply with GDPR. Note that this won't be sufficient in
    applications where users can store data in locations besides the
    default bucket.

Note that this script may not be necessary in all applications of
kinto-fxa.

"""

import itertools
import json
import logging
import uuid

import boto3
from ec2_metadata import ec2_metadata
from kinto.core.utils import hmac_digest
import transaction as current_transaction

logger = logging.getLogger(__name__)


def get_default_bucket_id(config, uid):
    secret = config['registry'].settings['userid_hmac_secret']
    digest = hmac_digest(secret, uid)
    return str(uuid.UUID(digest[:32]))


def process_account_events(config, queue_name, aws_region=None,
                           queue_wait_time=20):
    """Process account events from an SQS queue.

    This function polls the specified SQS queue for account-related events,
    processing each as it is found.  It polls indefinitely and does not return;
    to interrupt execution you'll need to e.g. SIGINT the process.
    """
    logger.info("Processing account events from %s", queue_name)
    try:
        # Connect to the SQS queue.
        # If no region is given, infer it from the instance metadata.
        if aws_region is None:
            logger.debug("Finding default region from instance metadata")
            aws_region = ec2_metadata.region

        logger.debug("Connecting to queue %r in %r", queue_name, aws_region)
        sqs = boto3.resource('sqs', region_name=aws_region)
        queue = sqs.get_queue_by_name(QueueName=queue_name)

        # Poll for messages indefinitely.
        # Use a wacky looping construct that can be mocked in tests.
        for x in itertools.count():
            msgs = queue.receive_messages(WaitTimeSeconds=queue_wait_time)
            for msg in msgs:
                process_account_event(config, msg.body)
                # This intentionally deletes the event even if it was some
                # unrecognized type.  No point leaving a backlog.
                msg.delete()

    except Exception:
        logger.exception("Error while processing account events")
        raise


def process_account_event(config, body):
    """Parse and process a single account event."""
    registry = config['registry']
    storage = registry.storage
    permission = registry.permission

    # Try very hard not to error out if there's junk in the queue.
    try:
        # Messages are a string of JSON, which, when parsed, has a
        # Message field, which is a string of JSON that actually
        # contains what we want.
        event = json.loads(body)
        event = json.loads(event['Message'])
        event_type = event["event"]
        uid = event["uid"]
    except (ValueError, KeyError) as e:
        logger.exception("Invalid account message: %r", e)
    else:
        if event_type == "delete":
            # Delete everything from storage and permissions for
            # this user.
            logger.info("Processing account delete for %r", uid)
            # FIXME: actually compute prefix correctly using
            # config instead of just hardcoding fxa
            uid = 'fxa:{}'.format(uid)
            default_bucket_id = get_default_bucket_id(config, uid)
            bucket_uri = '/buckets/{}'.format(default_bucket_id)
            logger.info('Deleting bucket %r', bucket_uri)
            # Delete the bucket and all its descendants.
            # This code is similar to that from kinto.views.buckets:on_buckets_deleted.
            for parent_id in [bucket_uri, bucket_uri + '/*']:
                storage.delete_all(
                    parent_id=parent_id,
                    collection_id=None,
                    with_deleted=False,
                )
                # Purge tombstones too.
                storage.purge_deleted(
                    parent_id=parent_id,
                    collection_id=None,
                )
                permission.delete_object_permissions(parent_id)
            current_transaction.commit()
        else:
            logger.warning("Dropping unknown event type %r",
                           event_type)
