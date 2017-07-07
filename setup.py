from setuptools import setup, find_packages

setup(
    name='pyntpg',
    version='0.1',
    author="Stefan Codrescu",
    author_email="stefan.codrescu@noaa.gov",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'netCDF4'
    ],
    entry_points='''
        [console_scripts]
        pyntpg=pyntpg.main:main
    ''',
    classifiers=[
        "Development Status :: 3 - Alpha",
    ]
)
