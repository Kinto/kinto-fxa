import cliquet
from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.interfaces import IAuthenticationPolicy, IAuthorizationPolicy

from cliquet_fxa import includeme
from cliquet_fxa.authentication import FxAOAuthAuthenticationPolicy

from . import unittest


class IncludeMeTest(unittest.TestCase):
    def test_settings_are_filled_with_defaults(self):
        config = testing.setUp()
        cliquet.initialize(config, '0.0.1')
        config.include(includeme)
        settings = config.get_settings()
        self.assertIsNotNone(settings.get('fxa-oauth.relier.enabled'))

    def test_a_default_authorization_is_set(self):
        config = testing.setUp()
        cliquet.initialize(config, '0.0.1')
        config.include(includeme)
        config.commit()
        policy = config.registry.queryUtility(IAuthorizationPolicy)
        self.assertTrue(isinstance(policy, ACLAuthorizationPolicy))

    def test_the_authentication_policy_is_set(self):
        config = testing.setUp()
        cliquet.initialize(config, '0.0.1')
        config.include(includeme)
        config.commit()
        policy = config.registry.queryUtility(IAuthenticationPolicy)
        self.assertTrue(isinstance(policy, FxAOAuthAuthenticationPolicy))

    def test_a_heartbeat_is_registered_at_oauth(self):
        config = testing.setUp()
        cliquet.initialize(config, '0.0.1')
        config.registry.heartbeats = {}
        config.include(includeme)
        self.assertIsNotNone(config.registry.heartbeats.get('oauth'))
