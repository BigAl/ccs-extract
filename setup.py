from setuptools import setup, find_packages

setup(
    name="ccs-extract",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pypdf>=3.0.0",
        "tqdm>=4.65.0",
        "jsonschema>=4.17.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "reportlab>=4.0.0",
        ],
    },
    python_requires=">=3.13",
    entry_points={
        "console_scripts": [
            "ccs-extract=ccs_extract:main",
        ],
    },
) 