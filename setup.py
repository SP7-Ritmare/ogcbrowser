import os
import stat
from codecs import open
from setuptools import setup, find_packages
from setuptools.command.install import install

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='ogcbrowser',
    version='1.0',
    description="ogcbrowser",
    long_description='ogcbrowser',
    url='https://github.com/SP7-Ritmare/',
    author='Stefano Menegon',
    author_email='stefano.menegon@ve.ismar.cnr.it',
    license="GPL3",
    # Full list of classifiers can be found at:
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
    ],
    keywords="OGC",
    packages=find_packages(),
    install_requires=[
    "django-overextends",
    "django-annoying",
    "django-rosetta",
    "django-grappelli==2.4.10",
    "djproxy",
    "Django"
    ],
    #
    include_package_data = True,
    setup_requires = [ "setuptools_git >= 0.3", ]
)
