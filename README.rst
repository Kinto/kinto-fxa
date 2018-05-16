Firefox Accounts support in Kinto
=================================

|travis| |master-coverage|

.. |travis| image:: https://travis-ci.org/Kinto/kinto-fxa.svg?branch=master
    :target: https://travis-ci.org/Kinto/kinto-fxa

.. |master-coverage| image::
    https://coveralls.io/repos/Kinto/kinto-fxa/badge.png?branch=master
    :alt: Coverage
    :target: https://coveralls.io/r/Kinto/kinto-fxa

*Kinto-fxa* enables authentication in *Kinto* applications using
*Firefox Accounts* OAuth2 bearer tokens.

N.B. This project used to be called *cliquet-fxa*, but was renamed to
  *kinto-fxa* following the rename of the *cliquet* project to
  *kinto*.

It provides:

* An authentication policy class;
* Integration with *Kinto* cache backend for token verifications;
* Integration with *Kinto* for heartbeat view checks;
* Some optional endpoints to perform the *OAuth* dance (*optional*).


* `Kinto documentation <http://kinto.readthedocs.io/en/latest/>`_
* `Issue tracker <https://github.com/Kinto/kinto-fxa/issues>`_


Installation
------------

As `stated in the official documentation <https://developer.mozilla.org/en-US/Firefox_Accounts>`_,
Firefox Accounts OAuth integration is currently limited to Mozilla relying services.

Install the Python package:

::

    pip install kinto-fxa


Include the package in the project configuration:

::

    kinto.includes = kinto_fxa

And configure authentication policy using `pyramid_multiauth
<https://github.com/mozilla-services/pyramid_multiauth#deployment-settings>`_ formalism:

::

    multiauth.policies = fxa
    multiauth.policy.fxa.use = kinto_fxa.authentication.FxAOAuthAuthenticationPolicy

By default, it will rely on the cache configured in *Kinto*.


Configuration
-------------

Fill those settings with the values obtained during the application registration:

::

    fxa-oauth.client_id = 89513028159972bc
    fxa-oauth.client_secret = 9aced230585cc0aaea0a3467dd800
    fxa-oauth.oauth_uri = https://oauth-stable.dev.lcip.org/v1
    fxa-oauth.requested_scope = profile kinto
    fxa-oauth.required_scope = kinto
    fxa-oauth.webapp.authorized_domains = *
    # fxa-oauth.cache_ttl_seconds = 300
    # fxa-oauth.state.ttl_seconds = 3600


In case the application shall not behave as a relier (a.k.a. OAuth dance
endpoints disabled):

::

    fxa-oauth.relier.enabled = false


If necessary, override default values for authentication policy:

::

    # multiauth.policy.fxa.realm = Realm

Handling multiple FxA clients
:::::::::::::::::::::::::::::

If you want to isolate data between two FxA apps using the same Kinto
service to sync their data you can define client specific
configuration:

::

    fxa-oauth.clients.notes.client_id = 89513028159972bc
    fxa-oauth.clients.notes.required_scope = profile app-notes

    fxa-oauth.clients.todo.client_id = 1805184631529d5a
    fxa-oauth.clients.todo.required_scope = profile app-todo


Depending on the requested scopes, Kinto Fxa will assign a user id or
another (using a suffix):

  - `fxa:{user_id}-notes` for the former
  - `fxa:{user_id}-todo` for the later

Note that you can still use `fxa:{user_id}` to explicitely share data between
apps for a given FxA user.

If you don't give any specific permission, it will be impossible for
someone logged in in with the `app-notes` scope in their Bearer token to
access the todo app data.

The default buckets will also be isolated, one for `notes` and one for
`todo`.

Login flow
----------

OAuth Bearer token
::::::::::::::::::

Use the OAuth token with this header:

::

    Authorization: Bearer <oauth_token>


:notes:

    If the token is not valid, this will result in a ``401`` error response.


Obtain token using Web UI
:::::::::::::::::::::::::

* Navigate the client to ``GET /fxa-oauth/login?redirect=http://app-endpoint/#``.
  There, a session cookie will be set, and the client will be redirected to a login
  form on the FxA content server;
* After submitting the credentials on the login page, the client will
  be redirected to ``http://app-endpoint/#{token}`` (the web-app).


Obtain token custom flow
::::::::::::::::::::::::

The ``GET /v1/fxa-oauth/params`` endpoint can be use to get the
configuration in order to trade the *Firefox Accounts* BrowserID with a
*Bearer Token*. `See Firefox Account documentation about this behavior
<https://developer.mozilla.org/en-US/Firefox_Accounts#Firefox_Accounts_BrowserID_API>`_

.. code-block:: http

    $ http GET http://localhost:8000/v0/fxa-oauth/params -v

    GET /v0/fxa-oauth/params HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0


    HTTP/1.1 200 OK
    Content-Length: 103
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 19 Feb 2015 09:28:37 GMT
    Server: waitress

    {
        "client_id": "89513028159972bc",
        "oauth_uri": "https://oauth-stable.dev.lcip.org",
        "scope": "profile"
    }


Scripts
-------

The ``kinto-fxa`` library installs a ``kinto-fxa`` command which is
used to run utility scripts that come with the ``kinto-fxa``
plugin. Right now the only one is ``process-account-events``, which
listens to an Amazon SQS queue for account deletion events and tries
to delete a user's data to comply with GDPR.

These scripts have some additional dependencies; you may need to ``pip
install kinto-fxa[scripts]`` to install them.

To use them, run ``kinto-fxa [script-name] [arguments]``.
