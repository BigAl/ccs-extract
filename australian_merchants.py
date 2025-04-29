"""
Standard Australian merchant patterns and categories for CCS-Extract.
"""

from typing import Dict, List, Tuple

# Standard Australian merchant patterns
STANDARD_MERCHANT_PATTERNS: List[Tuple[str, str]] = [
    # Major grocery chains
    (r'(?i)woolworths(?:\s+supermarket)?|woolies', 'Woolworths'),
    (r'(?i)coles(?:\s+supermarket)?', 'Coles'),
    (r'(?i)aldi(?:\s+store)?', 'Aldi'),
    (r'(?i)iga', 'IGA'),
    (r'(?i)nestle|nestlé|nestleau|nestleaust', 'Nestlé Australia'),
    
    # Major fuel stations
    (r'(?i)7-eleven|7 eleven|-eleven', '7-Eleven'),
    (r'(?i)bp|british petroleum', 'BP'),
    (r'(?i)shell', 'Shell'),
    (r'(?i)caltex', 'Caltex'),
    (r'(?i)united petroleum', 'United Petroleum'),
    
    # Major retail chains
    (r'(?i)bunnings|bunnings warehouse', 'Bunnings Warehouse'),
    (r'(?i)jb hi-fi|jb hifi|jbhifi|jb hi fi', 'JB Hi-Fi'),
    (r'(?i)harvey norman|harveynorman', 'Harvey Norman'),
    (r'(?i)the good guys|good guys', 'The Good Guys'),
    (r'(?i)officeworks', 'Officeworks'),
    (r'(?i)kmart', 'Kmart'),
    (r'(?i)target', 'Target'),
    (r'(?i)big w', 'Big W'),
    (r'(?i)david jones', 'David Jones'),
    (r'(?i)myer', 'Myer'),
    
    # Major utilities
    (r'(?i)origin energy', 'Origin Energy'),
    (r'(?i)agl', 'AGL'),
    (r'(?i)telstra', 'Telstra'),
    (r'(?i)optus', 'Optus'),
    
    # Major insurance companies
    (r'(?i)budget direct', 'Budget Direct'),
    (r'(?i)nrma', 'NRMA'),
    (r'(?i)racq', 'RACQ'),
    (r'(?i)racv', 'RACV'),
    (r'(?i)aami', 'AAMI'),
    
    # Major restaurants and cafes
    (r'(?i)soul\s*origin', 'Soul Origin'),
    (r'(?i)sushi\s*sushi', 'Sushi Sushi'),
    (r'(?i)subway', 'Subway'),
    
    # Generic patterns
    (r'(?i)supermarket', 'Generic Supermarket'),
    (r'(?i)restaurant|dining', 'Restaurant'),
    (r'(?i)cafe|coffee', 'Cafe'),
    (r'(?i)pub|tavern', 'Pub'),
    (r'(?i)pharmacy|chemist', 'Pharmacy'),
    (r'(?i)doctor|medical', 'Medical'),
    (r'(?i)school|college|university|tafe', 'Educational Institution'),
]

# Standard Australian transaction categories
STANDARD_CATEGORIES: Dict[str, List[str]] = {
    'Groceries': ['woolworths', 'coles', 'aldi', 'iga', 'supermarket', 'foodworks', 'nestle', 'nestlé', 'nestleau', 'nestleaust'],
    'Dining': ['restaurant', 'cafe', 'coffee', 'pub', 'tavern', 'bistro', 'soul origin', 'sushi sushi', 'subway'],
    'Transport': ['uber', 'taxi', 'cab', 'translink', 'go card', 'train', 'bus', 'parking'],
    'Entertainment': ['netflix', 'spotify', 'cinema', 'movie', 'theatre'],
    'Shopping': ['amazon', 'ebay', 'target', 'kmart', 'big w', 'david jones', 'myer', 'bunnings', 'jb hi-fi', 'harvey norman', 'officeworks'],
    'Utilities': ['origin energy', 'agl', 'telstra', 'optus', 'electricity', 'water', 'gas'],
    'Health': ['pharmacy', 'chemist', 'medical', 'doctor', 'dental'],
    'Education': ['university', 'school', 'college', 'tafe', 'course'],
    'Insurance': ['insurance', 'budget direct', 'nrma', 'racq', 'racv', 'aami'],
    'Fuel': ['7-eleven', 'bp', 'shell', 'caltex', 'united petroleum', 'petrol', 'service station'],
    'Holiday': ['hotel', 'motel', 'resort', 'vacation', 'holiday', 'accommodation'],
    'Other': []  # Default category
} 