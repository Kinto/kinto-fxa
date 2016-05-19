import kinto.core
import mock
from pyramid.exceptions import ConfigurationError
from pyramid import testing
from pyramid.config import Configurator

from kinto_fxa import includeme

from . import unittest


class IncludeMeTest(unittest.TestCase):
    def test_include_fails_if_kinto_was_not_initialized(self):
        config = testing.setUp()
        with self.assertRaises(ConfigurationError):
            config.include(includeme)

    def test_settings_are_filled_with_defaults(self):
        config = testing.setUp()
        kinto.core.initialize(config, '0.0.1')
        config.include(includeme)
        settings = config.get_settings()
        self.assertIsNotNone(settings.get('fxa-oauth.relier.enabled'))

    def test_a_heartbeat_is_registered_at_oauth(self):
        config = testing.setUp()
        kinto.core.initialize(config, '0.0.1')
        config.registry.heartbeats = {}
        config.include(includeme)
        self.assertIsNotNone(config.registry.heartbeats.get('oauth'))

    def test_warn_if_deprecated_settings_are_used(self):
        config = Configurator(settings={'fxa-oauth.scope': 'kinto'})
        with mock.patch('kinto_fxa.warnings.warn') as mocked:
            kinto.core.initialize(config, '0.0.1')
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
