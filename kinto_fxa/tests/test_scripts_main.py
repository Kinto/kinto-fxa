import mock
import unittest

from kinto_fxa.scripts import __main__ as main


class TestScripts(unittest.TestCase):
    def setUp(self):
        process_account_events_patcher = mock.patch(
            'kinto_fxa.scripts.__main__.process_account_events')
        self.process_account_events = process_account_events_patcher.start()
        self.addCleanup(process_account_events_patcher.stop)

        bootstrap_patcher = mock.patch('kinto_fxa.scripts.__main__.bootstrap')
        self.bootstrap = bootstrap_patcher.start()
        self.addCleanup(bootstrap_patcher.stop)

        self.config = mock.Mock()
        self.bootstrap.return_value = self.config

    def test_call_main(self):
        main.main(["process-account-events", "my-queue-name"])
        self.bootstrap.assert_called_with(main.DEFAULT_CONFIG_FILE)
        self.process_account_events.assert_called_with(
            self.config, 'my-queue-name', None, 20
        )
