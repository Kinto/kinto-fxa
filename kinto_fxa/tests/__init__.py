try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

from kinto.tests.core.support import DummyRequest  # NOQA
