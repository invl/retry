from setuptools import find_packages
from setuptools import setup


setup(
    packages=find_packages(),
    pbr=True,
    setup_requires=['pbr'],
)
