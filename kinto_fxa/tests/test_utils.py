import unittest

from pyramid.exceptions import ConfigurationError

from kinto_fxa.utils import parse_clients


class UtilsTest(unittest.TestCase):
    def test_parse_resources_raises_configuration_error_in_case_of_conflict(self):

        settings = {}
        settings['fxa-oauth.oauth_uri'] = 'https://oauth.accounts.firefox.com/v1'
        settings['fxa-oauth.cache_ttl_seconds'] = '0.01'
        settings['fxa-oauth.clients.notes.client_id'] = 'c73e46074a948932'
        settings['fxa-oauth.clients.notes.required_scope'] = (
            'https://identity.mozilla.org/apps/notes')
        settings['fxa-oauth.clients.lockbox.client_id'] = '299062f8b3838932'
        settings['fxa-oauth.clients.lockbox.required_scope'] = (
            'https://identity.mozilla.org/apps/notes')

        self.assertRaises(ConfigurationError, parse_clients, settings)
