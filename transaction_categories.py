"""
Transaction categorization and normalization rules for CCS-Extract.
"""

import re
from typing import Dict, List, Tuple

# Common merchant name patterns and their normalized names
MERCHANT_PATTERNS: List[Tuple[str, str]] = [
    # Grocery stores
    (r'(?i)woolworths|woolies', 'Woolworths'),
    (r'(?i)coles', 'Coles'),
    (r'(?i)aldi', 'Aldi'),
    (r'(?i)iga', 'IGA'),
    
    # Restaurants and cafes
    (r'(?i)cafe|coffee', 'Cafe'),
    (r'(?i)restaurant|dining', 'Restaurant'),
    (r'(?i)pub|tavern', 'Pub'),
    
    # Transport
    (r'(?i)uber', 'Uber'),
    (r'(?i)taxi|cab', 'Taxi'),
    (r'(?i)translink|go card', 'Public Transport'),
    
    # Online services
    (r'(?i)netflix', 'Netflix'),
    (r'(?i)spotify', 'Spotify'),
    (r'(?i)amazon', 'Amazon'),
    (r'(?i)apple\.com|itunes', 'Apple'),
    
    # Utilities
    (r'(?i)origin energy', 'Origin Energy'),
    (r'(?i)agl', 'AGL'),
    (r'(?i)telstra', 'Telstra'),
    (r'(?i)optus', 'Optus'),
]

# Transaction categories and their keywords
CATEGORIES: Dict[str, List[str]] = {
    'Groceries': ['woolworths', 'coles', 'aldi', 'iga', 'supermarket', 'foodworks'],
    'Dining': ['restaurant', 'cafe', 'coffee', 'pub', 'tavern', 'bistro'],
    'Transport': ['uber', 'taxi', 'cab', 'translink', 'go card', 'train', 'bus'],
    'Entertainment': ['netflix', 'spotify', 'cinema', 'movie', 'theatre'],
    'Shopping': ['amazon', 'ebay', 'target', 'kmart', 'big w', 'david jones', 'myer'],
    'Utilities': ['origin', 'agl', 'telstra', 'optus', 'electricity', 'gas', 'water'],
    'Health': ['pharmacy', 'chemist', 'medical', 'doctor', 'dental'],
    'Education': ['university', 'school', 'college', 'tafe', 'course'],
    'Insurance': ['insurance', 'nrma', 'racq', 'racv', 'aami'],
    'Other': []  # Default category
}

def normalize_merchant(description: str) -> str:
    """
    Normalize merchant names in transaction descriptions.
    
    Args:
        description (str): Original transaction description
        
    Returns:
        str: Normalized merchant name
    """
    for pattern, normalized in MERCHANT_PATTERNS:
        if re.search(pattern, description):
            return normalized
    return description

def categorize_transaction(description: str) -> str:
    """
    Categorize a transaction based on its description.
    
    Args:
        description (str): Transaction description
        
    Returns:
        str: Transaction category
    """
    description_lower = description.lower()
    
    for category, keywords in CATEGORIES.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    
    return 'Other' 