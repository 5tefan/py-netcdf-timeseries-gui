from setuptools import setup, find_packages

setup(
    name='pyntpg',
    version='0.3',
    author="Stefan Codrescu",
    author_email="stefan.codrescu@noaa.gov",
    packages=find_packages(),
    install_requires=[
        'ncagg',
        'numpy',
        'netCDF4',
        'cftime',
        'nc-time-axis'
    ],
    entry_points='''
        [console_scripts]
        pyntpg=pyntpg.main:main
    ''',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
