#!/bin/bash

# Run tests with coverage
pytest --cov=ccs_extract --cov=config --cov=logger --cov=exceptions --cov-report=term-missing test_ccs_extract.py 