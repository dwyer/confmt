import re

from distutils.core import setup

import simpleconf

name = 'simpleconf'
url = 'https://github.com/dwyer/%s' % name
download_url = '%s/tarball/%s' % (url, simpleconf.__version__)
author, author_email = re.match(r'^(.*) <(.*)>$',
                                simpleconf.__author__).groups()

kwargs = dict(
    name=name,
    packages=['.'],
    version=simpleconf.__version__,
    description='A simple configuration format encoder and decoder.',
    long_description=simpleconf.__doc__,
    author=author,
    author_email=author_email,
    url=url,
    download_url=download_url,
    keywords=[],
    classifiers=[], )

setup(**kwargs)
