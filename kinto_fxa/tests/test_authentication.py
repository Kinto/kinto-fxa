import gc
import time
import unittest

import mock
import requests
from kinto.core.cache import memory as memory_backend
from kinto.core.testing import DummyRequest
from fxa import errors as fxa_errors
from pyramid import httpexceptions

from kinto_fxa import authentication, DEFAULT_SETTINGS
from kinto_fxa.utils import parse_clients


class TokenVerificationCacheTest(unittest.TestCase):
    def setUp(self):
        cache = memory_backend.Cache(cache_prefix="tests",
                                     cache_max_size_bytes=float("inf"))
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

    def test_get_ignores_any_error(self):
        with mock.patch.object(self.cache.cache, 'get', side_effect=ValueError):
            retrieved = self.cache.get('foobar')
        self.assertIsNone(retrieved)

    def test_delete_ignores_any_error(self):
        self.cache.set('foobar', 'toto')
        with mock.patch.object(self.cache.cache, 'delete', side_effect=ValueError):
            self.cache.delete('foobar')
        retrieved = self.cache.get('foobar')
        self.assertIsNotNone(retrieved)

    def test_set_ignores_any_error(self):
        with mock.patch.object(self.cache.cache, 'set', side_effect=ValueError):
            self.cache.set('foobar', 'toto')
        retrieved = self.cache.get('foobar')
        self.assertIsNone(retrieved)


class FxAOAuthAuthenticationPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = authentication.FxAOAuthAuthenticationPolicy()
        self.backend = memory_backend.Cache(cache_prefix="tests",
                                            cache_max_size_bytes=float("inf"))

        self.request = self._build_request()
        self.profile_data = {
            "user": "33",
            "scope": ["profile", "mandatory", "optional"],
            "client_id": ""
        }

    def tearDown(self):
        self.backend.flush()

    def _build_request(self):
        request = DummyRequest()
        request.bound_data = {}
        request.registry.cache = self.backend
        settings = DEFAULT_SETTINGS.copy()
        settings['fxa-oauth.cache_ttl_seconds'] = '0.01'
        settings['fxa-oauth.required_scope'] = 'mandatory profile'
        request.registry.settings = settings
        resources, scope_routing = parse_clients(settings)
        request.registry._fxa_oauth_config = resources
        request.registry._fxa_oauth_scope_routing = scope_routing
        request.headers['Authorization'] = 'Bearer foo'
        return request

    def test_returns_none_if_authorization_header_is_missing(self):
        self.request.headers.pop('Authorization')
        user_id = self.policy.unauthenticated_userid(self.request)
        self.assertIsNone(user_id)

    def test_returns_none_if_token_is_malformed(self):
        self.request.headers['Authorization'] = 'Bearerfoo'
        user_id = self.policy.unauthenticated_userid(self.request)
        self.assertIsNone(user_id)

    def test_returns_none_if_token_is_unknown(self):
        self.request.headers['Authorization'] = 'Carrier foo'
        user_id = self.policy.authenticated_userid(self.request)
        self.assertIsNone(user_id)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_returns_fxa_userid(self, api_mocked):
        api_mocked.return_value = self.profile_data
        user_id = self.policy.authenticated_userid(self.request)
        self.assertEqual("33", user_id)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_returns_fxa_userid_in_principals(self, api_mocked):
        api_mocked.return_value = self.profile_data
        principals = self.policy.effective_principals(self.request)
        self.assertIn("33", principals)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_oauth_verification_is_cached(self, api_mocked):
        # Timing of this test is important. Force a collection to
        # ensure it doesn't happen in between requests.
        gc.collect()
        api_mocked.return_value = self.profile_data
        # First request from client.
        request = self._build_request()
        self.policy.authenticated_userid(request)
        # Second request from same client.
        request = self._build_request()
        self.policy.authenticated_userid(request)
        # Cache backend was used.
        self.assertEqual(1, api_mocked.call_count)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_oauth_verification_is_done_once_per_request(self, api_mocked):
        api_mocked.return_value = self.profile_data
        # First request from client.
        self.policy.authenticated_userid(self.request)
        # Within the same request cycle, token won't be verified.
        self.request.headers['Authorization'] = 'Bearer another'
        self.policy.authenticated_userid(self.request)
        # Request bound data is used.
        self.assertEqual(1, api_mocked.call_count)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_oauth_verification_uses_cache_by_token(self, api_mocked):
        api_mocked.return_value = self.profile_data
        # First request from client.
        request = self._build_request()
        self.policy.authenticated_userid(request)
        # Second request from another client.
        request = self._build_request()
        request.headers['Authorization'] = 'Bearer another'
        self.policy.authenticated_userid(request)
        # Cache backend key was different.
        self.assertEqual(2, api_mocked.call_count)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_oauth_verification_cache_has_ttl(self, api_mocked):
        api_mocked.return_value = self.profile_data
        # First request from client.
        request = self._build_request()
        self.policy.authenticated_userid(request)
        # Second request from same client after TTL.
        time.sleep(0.02)
        request = self._build_request()
        self.policy.authenticated_userid(request)
        # Cache backend key was expired.
        self.assertEqual(2, api_mocked.call_count)

    def test_raise_error_if_oauth2_server_misbehaves(self):
        with mock.patch('kinto_fxa.authentication.'
                        'OAuthClient.verify_token') as mocked:
            mocked.side_effect = fxa_errors.OutOfProtocolError
            self.assertRaises(httpexceptions.HTTPServiceUnavailable,
                              self.policy.authenticated_userid,
                              self.request)

    def test_returns_none_if_oauth2_error(self):
        with mock.patch('kinto_fxa.authentication.'
                        'OAuthClient.verify_token') as mocked:
            mocked.side_effect = fxa_errors.ClientError
            self.assertIsNone(self.policy.authenticated_userid(self.request))

    def test_returns_none_if_oauth2_scope_mismatch(self):
        with mock.patch('kinto_fxa.authentication.'
                        'OAuthClient.verify_token') as mocked:
            mocked.side_effect = fxa_errors.TrustError
            self.assertIsNone(self.policy.authenticated_userid(self.request))

    def test_forget_uses_realm(self):
        policy = authentication.FxAOAuthAuthenticationPolicy(realm='Who')
        headers = policy.forget(self.request)
        self.assertEqual(headers[0],
                         ('WWW-Authenticate', 'Bearer realm="Who"'))


class FxAPingTest(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.request.registry.settings = DEFAULT_SETTINGS
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


class FxAOAuthAuthenticationMultipleClientsPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = authentication.FxAOAuthAuthenticationPolicy()
        self.backend = memory_backend.Cache(cache_prefix="tests",
                                            cache_max_size_bytes=float("inf"))

        self.request = self._build_request()

        self.profile_data = {
            "user": "33",
            "scope": ["profile", "https://identity.mozilla.org/apps/notes"],
            "client_id": "c73e46074a948932"
        }

    def tearDown(self):
        self.backend.flush()

    def _build_request(self):
        request = DummyRequest()
        request.bound_data = {}
        request.registry.cache = self.backend
        settings = DEFAULT_SETTINGS.copy()
        settings['fxa-oauth.oauth_uri'] = 'https://oauth.accounts.firefox.com/v1'
        settings['fxa-oauth.cache_ttl_seconds'] = '0.01'
        settings['fxa-oauth.clients.notes.client_id'] = 'c73e46074a948932'
        settings['fxa-oauth.clients.notes.required_scope'] = (
            'profile https://identity.mozilla.org/apps/notes')
        settings['fxa-oauth.clients.lockbox.client_id'] = '299062f8b3838932'
        settings['fxa-oauth.clients.lockbox.required_scope'] = (
            'profile https://identity.mozilla.org/apps/lockbox')

        request.registry.settings = settings
        resources, scope_routing = parse_clients(settings)
        request.registry._fxa_oauth_config = resources
        request.registry._fxa_oauth_scope_routing = scope_routing
        request.headers['Authorization'] = 'Bearer foo'
        return request

    @mock.patch('fxa.oauth.APIClient.post')
    def test_returns_fxa_userid_for_notes(self, api_mocked):
        api_mocked.return_value = self.profile_data
        user_id = self.policy.authenticated_userid(self.request)
        self.assertEqual("33-notes", user_id)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_returns_fxa_userid_in_principals_for_notes(self, api_mocked):
        api_mocked.return_value = self.profile_data
        principals = self.policy.effective_principals(self.request)
        self.assertIn("fxa:33", principals)
        self.assertNotIn("33", principals)
        self.assertIn("33-notes", principals)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_fails_to_match_a_client_if_only_one_of_the_required_scopes(self, api_mocked):
        api_mocked.return_value = {
            "user": "33",
            "scope": ["profile"],
            "client_id": ""
        }
        user_id = self.policy.authenticated_userid(self.request)
        self.assertEqual(user_id, None)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_returns_fxa_userid_for_lockbox(self, api_mocked):
        api_mocked.return_value = {
            "user": "33",
            "scope": ["profile", "https://identity.mozilla.org/apps/lockbox"],
            "client_id": ""
        }
        user_id = self.policy.authenticated_userid(self.request)
        self.assertEqual("33-lockbox", user_id)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_returns_fxa_userid_in_principals_for_lockbox(self, api_mocked):
        api_mocked.return_value = {
            "user": "33",
            "scope": ["profile", "https://identity.mozilla.org/apps/lockbox"],
            "client_id": ""
        }
        principals = self.policy.effective_principals(self.request)
        self.assertIn("fxa:33", principals)
        self.assertNotIn("33", principals)
        self.assertIn("33-lockbox", principals)

    @mock.patch('fxa.oauth.APIClient.post')
    def test_fails_to_connect_if_bearer_matches_multiple_config(self, api_mocked):
        api_mocked.return_value = {
            "user": "33",
            "scope": ["profile", "https://identity.mozilla.org/apps/notes",
                      "https://identity.mozilla.org/apps/lockbox"],
            "client_id": ""
        }
        principals = self.policy.effective_principals(self.request)
        self.assertNotIn("fxa:33", principals)
        self.assertNotIn("33-lockbox", principals)
        self.assertNotIn("33-notes", principals)
