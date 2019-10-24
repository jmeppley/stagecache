import glob
from jme.stagecache import VERSION
from setuptools import setup, find_namespace_packages

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
	  packages=find_namespace_packages(include=['jme.*']),
      scripts=['stagecache'],
      install_requires=['paramiko', 'pyyaml', 'docopt'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT',
          'Natural Language :: English',
          'Programming Language :: Python :: 3.7'],
      )
