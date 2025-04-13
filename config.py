"""
Configuration settings for CCS-Extract.
"""

import re
from datetime import datetime
from typing import Dict, List, Pattern

# Date formats
DATE_FORMATS = {
    'input': '%d %b',  # Format in statement (without year)
    'output': '%d/%m/%Y'  # Desired output format
}

# Transaction patterns
TRANSACTION_PATTERNS: List[Dict[str, Pattern]] = [
    {
        'name': 'standard_with_year',
        'pattern': re.compile(r'(\d{1,2} [A-Za-z]{3} \d{4}) \$([\d,.]+)(.+)'),
        'groups': {
            'date': 1,
            'amount': 2,
            'description': 3
        }
    },
    {
        'name': 'standard_without_year',
        'pattern': re.compile(r'(\d{1,2} [A-Za-z]{3}) \$([\d,.]+)(.+)'),
        'groups': {
            'date': 1,
            'amount': 2,
            'description': 3
        }
    }
]

# CSV settings
CSV_SETTINGS = {
    'fieldnames': ['Transaction Date', 'Transaction Details', 'Amount'],
    'delimiter': ',',
    'quotechar': '"',
    'quoting': 'QUOTE_MINIMAL'
}

# Debug settings
DEBUG_SETTINGS = {
    'sample_text_length': 500,
    'page_separator': '--- PAGE {} ---\n'
}

# File settings
FILE_SETTINGS = {
    'encoding': 'utf-8',
    'output_suffix': '_transactions.csv',
    'debug_suffix': '_debug.txt'
}

# Logging settings
LOG_SETTINGS = {
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'level': 'INFO',
    'date_format': '%Y-%m-%d %H:%M:%S'
} 