Changelog
=========

This document describes changes between each past release.

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
