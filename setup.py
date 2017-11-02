from os.path import join
from shutil import copy
import sys

from setuptools import find_packages, setup



setup(

    # basic package metadata
    name='daskcluster',
    version="0.1",
    description='Create and manage Dask clusters',
    license='MIT',
    author='Iaroslav Shcherbatyi',
    author_email='info@anaconda.com',
    url='https://github.com/iaroslav-ai/dask-cluster',
    # details needed by setup
    install_requires=['boto3', 'joblib'],
    entry_points={
        'console_scripts': [
            'xcloud = daskcluster.cloudmanager:main',
            'xdask = daskcluster.daskmanager:main',
        ],
    },
)