from setuptools import setup, find_packages

setup(
    name="ccs-extract",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pypdf>=3.0.0",
        "tqdm>=4.66.0",
        "jsonschema>=4.21.0",
    ],
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=6.0.0',
            'coverage>=7.0.0',
        ],
    },
    python_requires=">=3.13",
) 