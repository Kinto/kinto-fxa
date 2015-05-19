import time

import mock
import requests
from cliquet.cache import memory as memory_backend
from fxa import errors as fxa_errors
from pyramid import httpexceptions

from cliquet_fxa import authentication

from . import unittest, DummyRequest


class TokenVerificationCacheTest(unittest.TestCase):
    def setUp(self):
        cache = memory_backend.Memory()
        self.cache = authentication.TokenVerificationCache(cache, 0.01)

    def test_set_adds_the_record(self):
        stored = 'toto'
        self.cache.set('foobar', stored)
        retrieved = self.cache.get('foobar')
        self.assertEquals(retrieved, stored)

    def test_delete_removes_the_record(self):
        self.cache.set('foobar', 'toto')
        self.cache.delete('foobar')
        retrieved = self.cache.get('foobar')
        self.assertIsNone(retrieved)

    def test_set_expires_the_value(self):
        self.cache.set('foobar', 'toto')
        time.sleep(0.02)
        retrieved = self.cache.get('foobar')
        self.assertIsNone(retrieved)


class FxAOAuthAuthenticationPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = authentication.FxAOAuthAuthenticationPolicy()
        self.backend = memory_backend.Memory()

        self.request = DummyRequest()
        self.request.registry.cache = self.backend
        self.request.registry.settings['fxa-oauth.cache_ttl_seconds'] = '0.01'
        self.request.headers['Authorization'] = 'Bearer foo'
        self.profile_data = {
            "user": "33", "scope": ["profile"], "client_id": ""
        }

    def tearDown(self):
        self.backend.flush()

    @mock.patch('fxa.oauth.APIClient.post')
    def test_prefixes_users_with_fxa(self, api_mocked):
        api_mocked.return_value = self.profile_data
        user_id = self.policy.unauthenticated_userid(self.request)
        self.assertEqual("fxa_33", user_id)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_oauth_verification_uses_cache(self, api_mocked):
        api_mocked.return_value = self.profile_data
        self.policy.unauthenticated_userid(self.request)
        self.policy.unauthenticated_userid(self.request)
        self.assertEqual(1, api_mocked.call_count)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_oauth_verification_cache_has_ttl(self, api_mocked):
        api_mocked.return_value = self.profile_data
        self.policy.unauthenticated_userid(self.request)
        time.sleep(0.02)
        self.policy.unauthenticated_userid(self.request)
        self.assertEqual(2, api_mocked.call_count)

    def test_raise_error_if_oauth2_server_misbehaves(self):
        with mock.patch('cliquet_fxa.authentication.'
                        'OAuthClient.verify_token') as mocked:
            mocked.side_effect = fxa_errors.OutOfProtocolError
            self.assertRaises(httpexceptions.HTTPServiceUnavailable,
                              self.policy.unauthenticated_userid,
                              self.request)

    def test_returns_none_if_oauth2_error(self):
        with mock.patch('cliquet_fxa.authentication.'
                        'OAuthClient.verify_token') as mocked:
            mocked.side_effect = fxa_errors.ClientError
            self.assertIsNone(self.policy.unauthenticated_userid(self.request))

    def test_returns_none_if_oauth2_scope_mismatch(self):
        with mock.patch('cliquet_fxa.authentication.'
                        'OAuthClient.verify_token') as mocked:
            mocked.side_effect = fxa_errors.TrustError
            self.assertIsNone(self.policy.unauthenticated_userid(self.request))


class FxAPingTest(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.request.registry.settings['fxa-oauth.oauth_uri'] = 'http://fxa'

    def test_returns_none_if_oauth_deactivated(self):
        self.request.registry.settings['fxa-oauth.oauth_uri'] = None
        self.assertIsNone(authentication.fxa_ping(self.request))

    @mock.patch('requests.get')
    def test_returns_true_if_ok(self, get_mocked):
        httpOK = requests.models.Response()
        httpOK.status_code = 200
        get_mocked.return_value = httpOK
        self.assertTrue(authentication.fxa_ping(self.request))

    @mock.patch('requests.get')
    def test_returns_false_if_ko(self, get_mocked):
        get_mocked.side_effect = requests.exceptions.HTTPError()
        self.assertFalse(authentication.fxa_ping(self.request))
