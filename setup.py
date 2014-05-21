from setuptools import setup


setup(
    name='retry',
    version='0.4.1',
    description='retry decorator',
    long_description=open('README.rst').read(),
    url='https://github.com/invl/retry',
    packages=['retry'],
    license='Apache License 2.0',
    install_requires=[
        'decorator',
    ]
)
