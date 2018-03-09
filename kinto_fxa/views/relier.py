import logging
import uuid
from urllib.parse import urlparse
from fnmatch import fnmatch

from cornice.validators import colander_validator
import colander
from fxa.oauth import Client as OAuthClient
from fxa import errors as fxa_errors

from pyramid import httpexceptions
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.settings import aslist

from kinto.core import Service
from kinto.core.errors import (
    http_error, ERRORS, json_error_handler, raise_invalid
)
from kinto.core.resource.schema import URL

from kinto_fxa.utils import fxa_conf


logger = logging.getLogger(__name__)


login = Service(name='fxa-oauth-login',
                path='/fxa-oauth/login',
                error_handler=json_error_handler)

token = Service(name='fxa-oauth-token',
                path='/fxa-oauth/token',
                error_handler=json_error_handler)


def persist_state(request):
    """Persist arbitrary string in cache.
    It will be matched when the user returns from the OAuth server login
    page.
    """
    state = uuid.uuid4().hex
    redirect_url = request.validated['querystring']['redirect']
    expiration = float(fxa_conf(request, 'cache_ttl_seconds'))

    cache = request.registry.cache
    cache.set(state, redirect_url, expiration)

    return state


class FxALoginQueryString(colander.MappingSchema):
    redirect = URL()


class FxALoginRequest(colander.MappingSchema):
    querystring = FxALoginQueryString()


def authorized_redirect(req, **kwargs):
    authorized = aslist(fxa_conf(req, 'webapp.authorized_domains'))
    if not req.validated:
        # Schema was not validated. Give up.
        return False

    redirect = req.validated['querystring']['redirect']

    domain = urlparse(redirect).netloc

    if not any((fnmatch(domain, auth) for auth in authorized)):
        req.errors.add('querystring', 'redirect',
                       'redirect URL is not authorized')


@login.get(schema=FxALoginRequest, permission=NO_PERMISSION_REQUIRED,
           validators=(colander_validator, authorized_redirect))
def fxa_oauth_login(request):
    """Helper to redirect client towards FxA login form."""
    state = persist_state(request)
    form_url = ('{oauth_uri}/authorization?action=signin'
                '&client_id={client_id}&state={state}&scope={scope}')
    scopes = fxa_conf(request, 'requested_scope')
    form_url = form_url.format(oauth_uri=fxa_conf(request, 'oauth_uri'),
                               client_id=fxa_conf(request, 'client_id'),
                               scope='+'.join(scopes.split()),
                               state=state)
    request.response.status_code = 302
    request.response.headers['Location'] = form_url

    return {}


class OAuthQueryString(colander.MappingSchema):
    code = colander.SchemaNode(colander.String())
    state = colander.SchemaNode(colander.String())


class OAuthRequest(colander.MappingSchema):
    querystring = OAuthQueryString()


@token.get(schema=OAuthRequest, permission=NO_PERMISSION_REQUIRED,
           validators=(colander_validator,))
def fxa_oauth_token(request):
    """Return OAuth token from authorization code.
    """
    state = request.validated['querystring']['state']
    code = request.validated['querystring']['code']

    # Require on-going session
    stored_redirect = request.registry.cache.get(state)

    # Make sure we cannot try twice with the same code
    request.registry.cache.delete(state)
    if not stored_redirect:
        error_msg = 'The OAuth session was not found, please re-authenticate.'
        return http_error(httpexceptions.HTTPRequestTimeout(),
                          errno=ERRORS.MISSING_AUTH_TOKEN,
                          message=error_msg)

    # Trade the OAuth code for a longer-lived token
    auth_client = OAuthClient(server_url=fxa_conf(request, 'oauth_uri'),
                              client_id=fxa_conf(request, 'client_id'),
                              client_secret=fxa_conf(request, 'client_secret'))
    try:
        token = auth_client.trade_code(code)
    except fxa_errors.OutOfProtocolError:
        raise httpexceptions.HTTPServiceUnavailable()
    except fxa_errors.InProtocolError as error:
        logger.error(error)
        error_details = {
            'name': 'code',
            'location': 'querystring',
            'description': 'Firefox Account code validation failed.'
        }
        raise_invalid(request, **error_details)

    return httpexceptions.HTTPFound(location='%s%s' % (stored_redirect, token))
