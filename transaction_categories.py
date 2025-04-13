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
    (r'(?i)nestle|nestlé|nestleau', 'Nestlé Australia'),
    (r'(?i)nespresso australia', 'Nespresso Australia'),
    
    # Restaurants and cafes
    (r'(?i)soul origin', 'Soul Origin'),
    (r'(?i)space kitchen', 'Space Kitchen'),
    (r'(?i)sushi sushi', 'Sushi Sushi'),
    (r'(?i)tfc sushi', 'TFC Sushi'),
    (r'(?i)zambrero', 'Zambrero'),
    (r'(?i)the spence grocer', 'The Spence Grocer'),
    (r'(?i)mcdonalds|mcdonald\'s|maccas', 'McDonald\'s'),
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
    (r'(?i)ticketek', 'Ticketek'),
    (r'(?i)hoyts', 'Hoyts'),
    (r'(?i)www\.endota\.com\.au', 'Endota Spa'),
    
    # Utilities
    (r'(?i)origin energy', 'Origin Energy'),
    (r'(?i)agl', 'AGL'),
    (r'(?i)telstra', 'Telstra'),
    (r'(?i)optus', 'Optus'),
    (r'(?i)belong', 'Belong'),
    
    # Fuel stations
    (r'(?i)7-eleven|7 eleven|-eleven', '7-Eleven'),
    (r'(?i)bp|british petroleum', 'BP'),
    (r'(?i)shell', 'Shell'),
    (r'(?i)caltex', 'Caltex'),
    (r'(?i)united petroleum', 'United Petroleum'),
    
    # Hotels
    (r'(?i)accor', 'Accor'),
    
    # Health
    (r'(?i)amcal|amcal pharmacy', 'Amcal Pharmacy'),
    (r'(?i)endota spa', 'Endota Spa'),
    
    # Hardware stores
    (r'(?i)bunnings|bunnings warehouse', 'Bunnings Warehouse'),
    (r'(?i)mitre 10|mitre10', 'Mitre 10'),
    (r'(?i)home hardware', 'Home Hardware'),
    (r'(?i)hardware store|hardware shop', 'Hardware Store'),
    
    # Electronics stores
    (r'(?i)jb hi-fi|jb hifi|jbhifi|jb hi fi', 'JB Hi-Fi'),
    (r'(?i)harvey norman|harveynorman', 'Harvey Norman'),
    (r'(?i)the good guys|good guys', 'The Good Guys'),
    (r'(?i)officeworks', 'Officeworks'),
    
    # Insurance companies
    (r'(?i)budget direct', 'Budget Direct'),
    (r'(?i)nrma', 'NRMA'),
    (r'(?i)racq', 'RACQ'),
    (r'(?i)racv', 'RACV'),
    (r'(?i)aami', 'AAMI'),
]

# Transaction categories and their keywords
CATEGORIES: Dict[str, List[str]] = {
    'Groceries': ['woolworths', 'coles', 'aldi', 'iga', 'supermarket', 'foodworks', 'nestle', 'nestlé', 'nestleau', 'nespresso australia'],
    'Dining': ['restaurant', 'cafe', 'coffee', 'pub', 'tavern', 'bistro', 'soul origin', 'space kitchen', 'sushi sushi', 'tfc sushi', 'zambrero', 'the spence grocer', 'mcdonalds', 'mcdonald\'s', 'maccas'],
    'Transport': ['uber', 'taxi', 'cab', 'translink', 'go card', 'train', 'bus'],
    'Entertainment': ['netflix', 'spotify', 'cinema', 'movie', 'theatre', 'ticketek', 'hoyts'],
    'Shopping': ['amazon', 'ebay', 'target', 'kmart', 'big w', 'david jones', 'myer', 'bunnings', 'mitre 10', 'home hardware', 'hardware store', 'hardware shop', 'jb hi-fi', 'jb hifi', 'jbhifi', 'jb hi fi', 'harvey norman', 'harveynorman', 'the good guys', 'good guys', 'officeworks'],
    'Utilities': ['origin energy', 'agl', 'telstra', 'optus', 'belong', 'electricity', 'water', 'gas'],
    'Health': ['pharmacy', 'chemist', 'medical', 'doctor', 'dental', 'amcal', 'endota spa', 'www.endota.com.au'],
    'Education': ['university', 'school', 'college', 'tafe', 'course'],
    'Insurance': ['insurance', 'budget direct', 'nrma', 'racq', 'racv', 'aami'],
    'Fuel': ['7-eleven', '7 eleven', '-eleven', 'bp', 'shell', 'caltex', 'united petroleum', 'petrol', 'service station'],
    'Holiday': ['hotel', 'motel', 'resort', 'accor', 'vacation', 'holiday', 'accommodation'],
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
    # Remove Square payment prefix if present
    description = re.sub(r'^SQ \*', '', description)
    
    # Remove PayPal payment prefix if present
    description = re.sub(r'^PAYPAL \*', '', description)
    
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