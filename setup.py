import glob
from jme.stagecache import VERSION
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

DESCRIPTION = "Python module and script for staging files to cache dir"
LONG_DESCRIPTION = open('README.md').read()
NAME = "stagecache"
AUTHOR = "John Eppley"
AUTHOR_EMAIL = "jmeppley@gmail.edu"
MAINTAINER = "John Eppley"
MAINTAINER_EMAIL = "jmeppley@gmail.edu"
URL = 'https://github.com/jmeppley'
DOWNLOAD_URL = 'https://github.com/jmeppley/stagecache'
LICENSE = 'MIT'

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      maintainer=MAINTAINER,
      maintainer_email=MAINTAINER_EMAIL,
      url=URL,
      download_url=DOWNLOAD_URL,
      license=LICENSE,
      packages=['jme', ],
      scripts=[s for s in glob.glob('*.py')
               if s != 'setup.py'],
      install_requires=['paramiko', 'pyyaml'],
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT',
          'Natural Language :: English',
          'Programming Language :: Python :: 3.7'],
      )
