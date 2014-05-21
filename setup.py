from setuptools import setup


setup(
    name='retry',
    version='0.4.2',
    description='retry decorator',
    long_description=open('README.rst').read(),
    url='https://github.com/invl/retry',
    packages=['retry'],
    license='Apache License 2.0',
    install_requires=[
        'decorator',
    ],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ]
)
