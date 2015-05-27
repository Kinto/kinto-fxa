import cliquet
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.settings import asbool

from cliquet_fxa.authentication import fxa_ping, FxAOAuthAuthenticationPolicy


DEFAULT_SETTINGS = {
    'fxa-oauth.cache_ttl_seconds': 5 * 60,
    'fxa-oauth.client_id': None,
    'fxa-oauth.client_secret': None,
    'fxa-oauth.heartbeat_timeout_seconds': 3,
    'fxa-oauth.oauth_uri': None,
    'fxa-oauth.realm': 'Realm',
    'fxa-oauth.relier.enabled': True,
    'fxa-oauth.scope': 'profile',
    'fxa-oauth.state.ttl_seconds': 3600,  # 1 hour
    'fxa-oauth.webapp.authorized_domains': '',
}


def includeme(config):
    cliquet.load_default_settings(config, DEFAULT_SETTINGS)
    settings = config.get_settings()

    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)

    # Use the settings to construct an AuthenticationPolicy.
    realm = settings['fxa-oauth.realm']
    authn_policy = FxAOAuthAuthenticationPolicy(realm=realm)
    config.set_authentication_policy(authn_policy)

    if hasattr(config.registry, 'heartbeats'):
        config.registry.heartbeats['oauth'] = fxa_ping

    # Ignore FxA OAuth relier endpoint in case it's not activated.
    relier_enabled = asbool(settings['fxa-oauth.relier.enabled'])
    cache_enabled = hasattr(config.registry, 'cache')
    kwargs = {}
    if not relier_enabled or not cache_enabled:
        kwargs['ignore'] = 'cliquet_fxa.views.relier'
    config.scan('cliquet_fxa.views', **kwargs)
