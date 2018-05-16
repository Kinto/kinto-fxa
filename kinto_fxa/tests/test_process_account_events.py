import json
import mock
import unittest

from kinto_fxa.scripts.process_account_events import (
    get_default_bucket_id,
    process_account_event,
    process_account_events,
)


class TestProcessAccountEvent(unittest.TestCase):
    def setUp(self):
        self.registry = mock.Mock()
        self.registry.settings = {
            'userid_hmac_secret': 'efghi'
        }
        self.config = {"registry": self.registry}
        self.uid = 'abcd'
        # Computed this by hand in the Python terminal
        self.bucket_id = '719b8628-0230-7b89-46e8-a365d68a66d1'
        self.real_message = json.dumps({
            "Message": json.dumps({
                "event": "delete",
                "uid": self.uid,
            })
        })

    @mock.patch('kinto_fxa.scripts.process_account_events.logger')
    def test_message_that_isnt_json_is_dropped(self, logger):
        process_account_event(self.config, "blah")
        calls = logger.exception.call_args_list
        self.assertEqual(len(calls), 1)
        args = calls[0][0]
        self.assertEqual(args[0], "Invalid account message: %r")
        self.assert_(isinstance(args[1], Exception))

    @mock.patch('kinto_fxa.scripts.process_account_events.logger')
    def test_invalid_message_is_dropped(self, logger):
        process_account_event(self.config, "{\"Message\": \"{\\\"event\\\": \\\"delete\\\"}\"}")
        calls = logger.exception.call_args_list
        self.assertEqual(len(calls), 1)
        args = calls[0][0]
        self.assertEqual(args[0], "Invalid account message: %r")
        self.assert_(isinstance(args[1], KeyError))

    @mock.patch('kinto_fxa.scripts.process_account_events.logger')
    def test_unknown_message_type_is_dropped(self, logger):
        process_account_event(self.config, json.dumps({
            "Message": json.dumps({
                "event": "rezone",
                "uid": "abcd",
            })
        }))
        logger.warning.assert_called_with(
            "Dropping unknown event type %r",
            "rezone"
        )

    def test_get_default_bucket_id(self):
        self.assertEqual(get_default_bucket_id(self.config, self.uid),
                         self.bucket_id)

    @mock.patch('kinto_fxa.scripts.process_account_events.get_default_bucket_id')
    def test_valid_message_calls_deletes(self, get_default_bucket_id):
        get_default_bucket_id.return_value = 'some_fxa_bucket'
        process_account_event(self.config, self.real_message)
        self.registry.storage.delete_all.assert_any_call(
            parent_id='/buckets/some_fxa_bucket',
            collection_id=None,
            with_deleted=False,
        )
        self.registry.storage.purge_deleted.assert_any_call(
            parent_id='/buckets/some_fxa_bucket'.format(self.bucket_id),
            collection_id=None,
        )
        self.registry.storage.delete_all.assert_any_call(
            parent_id='/buckets/some_fxa_bucket/*'.format(self.bucket_id),
            collection_id=None,
            with_deleted=False,
        )
        self.registry.storage.purge_deleted.assert_any_call(
            parent_id='/buckets/some_fxa_bucket/*'.format(self.bucket_id),
            collection_id=None,
        )
        self.registry.permission.delete_object_permissions.assert_any_call(
            '/buckets/some_fxa_bucket'.format(self.bucket_id)
        )
        self.registry.permission.delete_object_permissions.assert_any_call(
            '/buckets/some_fxa_bucket/*'.format(self.bucket_id)
        )


class TestProcessAccountEvents(unittest.TestCase):
    def setUp(self):
        boto3_patcher = mock.patch('kinto_fxa.scripts.process_account_events.boto3')
        self.boto3 = boto3_patcher.start()
        self.addCleanup(boto3_patcher.stop)

        self.sqs = mock.Mock()
        self.boto3.resource.return_value = self.sqs

        self.queue = mock.Mock()
        self.sqs.get_queue_by_name.return_value = self.queue

        ec2_metadata_patcher = mock.patch('kinto_fxa.scripts.process_account_events.ec2_metadata')
        self.ec2 = ec2_metadata_patcher.start()
        self.addCleanup(ec2_metadata_patcher.stop)

        self.config = mock.Mock()

    @mock.patch('kinto_fxa.scripts.process_account_events.itertools')
    def test_gets_sqs_queue(self, itertools):
        itertools.count.return_value = [1]

        self.queue.receive_messages.return_value = []
        process_account_events(self.config, 'my-queue-name', 'my-aws-region', 23)
        self.boto3.resource.assert_called_with('sqs', region_name='my-aws-region')
        self.sqs.get_queue_by_name.assert_called_with(QueueName='my-queue-name')
        self.queue.receive_messages.assert_called_with(WaitTimeSeconds=23)

    @mock.patch('kinto_fxa.scripts.process_account_events.process_account_event')
    @mock.patch('kinto_fxa.scripts.process_account_events.itertools.count')
    def test_processes_each_message(self, count, process_account_event):
        count.return_value = [1]

        message = mock.Mock(body="my-body")
        self.queue.receive_messages.return_value = [message]

        process_account_events(self.config, 'my-queue-name', 'my-aws-region', 23)
        process_account_event.assert_called_with(self.config, 'my-body')
        message.delete.assert_called_with()

    @mock.patch('kinto_fxa.scripts.process_account_events.logger')
    @mock.patch('kinto_fxa.scripts.process_account_events.process_account_event')
    @mock.patch('kinto_fxa.scripts.process_account_events.itertools.count')
    def test_exceptions_when_processing_messages_are_logged(
            self, count, process_account_event, logger):
        count.return_value = [1]

        message = mock.Mock(body="my-body")
        self.queue.receive_messages.return_value = [message]
        process_account_event.side_effect = ValueError

        with self.assertRaises(ValueError):
            process_account_events(self.config, 'my-queue-name', 'my-aws-region', 23)

        logger.exception.assert_called_with("Error while processing account events")

    @mock.patch('kinto_fxa.scripts.process_account_events.itertools')
    def test_gets_ec2_metadata_if_no_region_given(self, itertools):
        itertools.count.return_value = [1]
        self.ec2.region = 'region-from-metadata'
        self.queue.receive_messages.return_value = []
        process_account_events(self.config, 'my-queue-name', None, 23)
        self.boto3.resource.assert_called_with('sqs', region_name='region-from-metadata')
