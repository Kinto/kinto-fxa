import cliquet
import mock
from pyramid import testing
from pyramid.config import Configurator

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

    def test_warn_if_deprecated_settings_are_used(self):
        config = Configurator(settings={'fxa-oauth.scope': 'kinto'})
        with mock.patch('cliquet_fxa.warnings.warn') as mocked:
            cliquet.initialize(config, '0.0.1')
            config.include(includeme)
            msg = ('"fxa-oauth.scope" is now deprecated. Please use '
                   '"fxa-oauth.requested_scope" and '
                   '"fxa-oauth.required_scope" instead.')
            mocked.assert_called_with(msg, DeprecationWarning)
        settings = config.get_settings()
        self.assertIn('fxa-oauth.requested_scope', settings)
        self.assertEqual(settings['fxa-oauth.requested_scope'], 'kinto')
        self.assertIn('fxa-oauth.required_scope', settings)
        self.assertEqual(settings['fxa-oauth.required_scope'], 'kinto')
