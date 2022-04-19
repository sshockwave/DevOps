from setuptools import setup

setup(
    name='rindex',
    version='0.0.1',
    packages=['rindex'],
    # ...
    entry_points={
        'console_scripts': [
            'rindex=rindex.cli:main',
        ]
    }
)
