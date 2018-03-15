import pkg_resources
import warnings

from pyramid.exceptions import ConfigurationError
from pyramid.settings import asbool

from kinto_fxa.authentication import fxa_ping
from kinto_fxa.utils import parse_clients

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version


DEFAULT_SETTINGS = {
    'fxa-oauth.cache_ttl_seconds': 5 * 60,
    'fxa-oauth.client_id': None,
    'fxa-oauth.client_secret': None,
    'fxa-oauth.heartbeat_timeout_seconds': 3,
    'fxa-oauth.oauth_uri': None,
    'fxa-oauth.relier.enabled': True,
    'fxa-oauth.requested_scope': 'profile',
    'fxa-oauth.required_scope': None,
    'fxa-oauth.state.ttl_seconds': 3600,  # 1 hour
    'fxa-oauth.webapp.authorized_domains': '',
}


def includeme(config):
    if not hasattr(config.registry, 'heartbeats'):
        message = ('kinto-fxa should be included once Kinto is initialized'
                   ' . Use setting ``kinto.includes`` instead of '
                   '``pyramid.includes`` or include it manually.')
        raise ConfigurationError(message)

    settings = config.get_settings()

    defaults = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in settings}
    config.add_settings(defaults)

    if 'fxa-oauth.scope' in settings:
        message = ('"fxa-oauth.scope" is now deprecated. Please use '
                   '"fxa-oauth.requested_scope" and '
                   '"fxa-oauth.required_scope" instead.')
        warnings.warn(message, DeprecationWarning)

        settings['fxa-oauth.requested_scope'] = settings['fxa-oauth.scope']
        settings['fxa-oauth.required_scope'] = settings['fxa-oauth.scope']

    resources, scope_routing = parse_clients(settings)
    config.registry._fxa_oauth_config = resources
    config.registry._fxa_oauth_scope_routing = scope_routing

    # Register heartbeat to ping FxA server.
    config.registry.heartbeats['oauth'] = fxa_ping

    config.add_api_capability(
        "fxa",
        version=__version__,
        description="You can authenticate to that server "
                    "using Firefox Account.",
        url="https://github.com/Kinto/kinto-fxa")

    # Ignore FxA OAuth relier endpoint in case it's not activated.
    relier_enabled = asbool(settings['fxa-oauth.relier.enabled'])
    kwargs = {}
    if not relier_enabled:
        kwargs['ignore'] = 'kinto_fxa.views.relier'
    config.scan('kinto_fxa.views', **kwargs)
