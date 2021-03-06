Changelog
=========

This document describes changes between each past release.

2.6.0 (unreleased)
------------------

- Nothing changed yet.


2.5.3 (2019-07-02)
------------------

**Optimization**

- Try to keep ``OAuthClient`` around longer to take advantage of HTTP keepalives (#133).


2.5.2 (2018-07-05)
------------------

**Bug fixes**

- Fix the ``process-account-events`` script to take client user ID suffixes into account (fixes #61)


2.5.1 (2018-06-28)
------------------

- Set up metrics on the ``process-account-events`` script (#57).
- Set up logging on the ``kinto_fxa.scripts`` programs (#58).


2.5.0 (2018-05-17)
------------------

- Introduce new ``kinto_fxa.scripts``. Right now the only script
  available is ``process-account-events``, which listens to an SQS
  queue for user delete events and deletes data from that user's
  default bucket, in order to comply with GDPR.


2.4.1 (2018-03-15)
------------------

- Move kinto-fxa to the Kinto github org. (#54)


2.4.0 (2017-11-27)
------------------

- Add support for multiple FxA Clients (#52)


2.3.1 (2017-01-30)
------------------

**Bug fixes**

- Make sure that caching of token verification nevers prevents from authenticating
  requests (see Mozilla/PyFxA#48)


2.3.0 (2016-12-22)
------------------

**Internal changes**

- Migrate schemas to Cornice 2 #38


2.2.0 (2016-10-27)
------------------

**New features**

- Improve FxA error messages (fixes #1)

**Bug fixes**

- Optimize authentication policy to avoid validating the token several times
  per request (fixes #33)

**Internal changes**

- Use Service from kinto.core (fixes #28)
- Make sure it does not catch Cornice 2 dependency (#36)


2.1.0 (2016-09-08)
------------------

- Add the plugin version in the capability.


2.0.0 (2016-05-19)
------------------

**Breaking changes**

- Project renamed to *Kinto-fxa* to match the rename of ``cliquet`` to
  ``kinto.core``.

- Update to ``kinto.core`` for compatibility with Kinto 3.0. This
  release is no longer compatible with Kinto < 3.0, please upgrade!

- With *Kinto* > 2.12*, the setting ``multiauth.policy.fxa.use`` must now
  be explicitly set to ``kinto_fxa.authentication.FxAOAuthAuthenticationPolicy``

**Bug fixes**

- Fix checking of ``Authorization`` header when python is ran ``-O``
  (ref mozilla-services/cliquet#592)


1.4.0 (2015-10-28)
------------------

-  Updated to *Cliquet* 2.9.0

**Breaking changes**

- *cliquet-fxa* cannot be included using ``pyramid.includes`` setting.
  Use ``cliquet.includes`` instead.


1.3.2 (2015-10-22)
------------------

**Bug fixes**

- In case the Oauth dance is interrupted, return a ``408 Request Timeout``
  error instead of the ``401 Unauthenticated`` one. (#11)
- Do not call ``cliquet.load_default_settings`` from cliquet-fxa (#12)


1.3.1 (2015-09-29)
------------------

- Separate multiple scopes by a + in login URL.


1.3.0 (2015-09-29)
------------------

**Bug fixes**

- Multiple scopes can be requested on the login flow.
- Multiple scopes can be required for the app.

**Configuration changes**

- ``fxa-oauth.scope`` is now deprecated. ``fxa-oauth.requested_scope`` and
  ``fxa-oauth.required_scope`` should be used instead.


1.2.0 (2015-06-24)
------------------

- Add default settings to define a policy "fxa".
  It is now possible to just include ``cliquet_fxa`` and
  add ``fxa`` to ``multiauth.policies`` setting list.
- Do not check presence of cliquet cache in initialization
  phase.
- Do not use Cliquet logger to prevent initialization errors.


1.1.0 (2015-06-18)
------------------

- Do not prefix authenticated user with ``fxa_`` anymore (#5)


1.0.0 (2015-06-09)
------------------

- Imported code from *Cliquet*
