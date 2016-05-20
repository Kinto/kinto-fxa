Changelog
=========

This document describes changes between each past release.

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
