from setuptools import setup, find_packages

setup(
    name='swapify',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'swap=swapify.cli:main',
        ],
    },
    install_requires=[
        'requests',
    ],
)