import cliquet
import warnings
from pyramid.settings import asbool

from cliquet_fxa.authentication import fxa_ping


DEFAULT_SETTINGS = {
    'multiauth.policy.fxa.use': ('cliquet_fxa.authentication.'
                                 'FxAOAuthAuthenticationPolicy'),
    'multiauth.policy.fxa.realm': 'Realm',
    'fxa-oauth.cache_ttl_seconds': 5 * 60,
    'fxa-oauth.client_id': None,
    'fxa-oauth.client_secret': None,
    'fxa-oauth.heartbeat_timeout_seconds': 3,
    'fxa-oauth.oauth_uri': None,
    'fxa-oauth.relier.enabled': True,
    'fxa-oauth.requested_scope': 'profile',
    'fxa-oauth.required_scope': 'profile',
    'fxa-oauth.state.ttl_seconds': 3600,  # 1 hour
    'fxa-oauth.webapp.authorized_domains': '',
}


def includeme(config):
    cliquet.load_default_settings(config, DEFAULT_SETTINGS)
    settings = config.get_settings()

    if 'fxa-oauth.scope' in settings:
        message = ('"fxa-oauth.scope" is now deprecated. Please use '
                   '"fxa-oauth.requested_scope" and '
                   '"fxa-oauth.required_scope" instead.')
        warnings.warn(message, DeprecationWarning)

        settings['fxa-oauth.requested_scope'] = settings['fxa-oauth.scope']
        settings['fxa-oauth.required_scope'] = settings['fxa-oauth.scope']

    # Register heartbeat to ping FxA server.
    if hasattr(config.registry, 'heartbeats'):
        config.registry.heartbeats['oauth'] = fxa_ping

    # Requires cornice to scan views.
    config.include("cornice")

    # Ignore FxA OAuth relier endpoint in case it's not activated.
    relier_enabled = asbool(settings['fxa-oauth.relier.enabled'])
    kwargs = {}
    if not relier_enabled:
        kwargs['ignore'] = 'cliquet_fxa.views.relier'
    config.scan('cliquet_fxa.views', **kwargs)
