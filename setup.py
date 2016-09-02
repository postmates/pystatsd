import os
from setuptools import setup


# Utility function to read the README.md file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="pystatsd",
    version="2.0.0",
    author="John Koenig",
    author_email="john@postmates.com",
    description=("One-liner statsd API"),
    license="MIT",
    keywords="python statsd",
    url="https://github.com/postmates/pystatsd",
    packages=['pystatsd'],
    install_requires=[
    ],
    long_description=read('README.md'),
    classifiers=[
        "Topic :: Utilities",
    ],
)
