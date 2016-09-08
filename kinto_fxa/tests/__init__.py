try:
    from kinto.core.testing import DummyRequest
except ImportError:
    # Kinto < 4
    from kinto.tests.core.support import DummyRequest


__all__ = ('DummyRequest', )
