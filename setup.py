import re
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
      name="gql-relay-result",
      author="UniversalAppfactory",
      author_email="info@universalappfactory.de",
      description="Pageable resultset for gql queries",
      long_description=long_description,
      long_description_content_type="text/markdown",
      version='0.0.3',
      url="https://github.com/universalappfactory/gql-relay-result",
      packages=find_packages(exclude=['tests', 'tests.*']),
      install_requires=[
        'gql>=3.0.0a4',
      ],
      keywords="api graphql protocol rest relay gql client",
      classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
      ],
      python_requires='>=3.6',
)