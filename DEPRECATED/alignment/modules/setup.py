from setuptools import setup

setup(
    name='pyMille',
    version='0.1',  # specified elsewhere
    packages=[''],
    package_dir={'': './build'},
    package_data={'': ['pyMille*.so']},
)