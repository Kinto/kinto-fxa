import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    README = f.read()

with codecs.open(os.path.join(here, 'CHANGELOG.rst'), encoding='utf-8') as f:
    CHANGELOG = f.read()

with codecs.open(os.path.join(here, 'CONTRIBUTORS.rst'),
                 encoding='utf-8') as f:
    CONTRIBUTORS = f.read()


REQUIREMENTS = [
    'kinto >= 2.9',
    'pyfxa >= 0.0.9',
]

DEPENDENCY_LINKS = []

ENTRY_POINTS = {}


setup(name='kinto-fxa',
      version='2.0.0',
      description='Firefox Accounts support in Kinto',
      long_description=README + "\n\n" + CHANGELOG + "\n\n" + CONTRIBUTORS,
      license='Apache License (2.0)',
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "License :: OSI Approved :: Apache Software License"
      ],
      keywords="web services",
      author='Mozilla Services',
      author_email='services-dev@mozilla.com',
      url='https://github.com/mozilla-services/kinto-fxa',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      extras_require={},
      dependency_links=DEPENDENCY_LINKS,
      entry_points=ENTRY_POINTS)
