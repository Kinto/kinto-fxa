import cliquet
from pyramid import testing

from cliquet_fxa import includeme

from . import unittest


class IncludeMeTest(unittest.TestCase):
    def test_settings_are_filled_with_defaults(self):
        config = testing.setUp()
        cliquet.initialize(config, '0.0.1')
        config.include(includeme)
        settings = config.get_settings()
        self.assertIsNotNone(settings.get('fxa-oauth.relier.enabled'))

    def test_a_heartbeat_is_registered_at_oauth(self):
        config = testing.setUp()
        cliquet.initialize(config, '0.0.1')
        config.registry.heartbeats = {}
        config.include(includeme)
        self.assertIsNotNone(config.registry.heartbeats.get('oauth'))
