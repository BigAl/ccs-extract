"""
Transaction categorization and normalization rules for CCS-Extract.
"""

import re
import json
import os
from typing import Dict, List, Tuple
from jsonschema import validate, ValidationError

# JSON schema for configuration validation
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["merchant_patterns", "categories"],
    "properties": {
        "merchant_patterns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["pattern", "normalized"],
                "properties": {
                    "pattern": {"type": "string"},
                    "normalized": {"type": "string"}
                }
            }
        },
        "categories": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
}

# Default merchant patterns and categories
DEFAULT_MERCHANT_PATTERNS: List[Tuple[str, str]] = [
    # Grocery stores
    (r'(?i)woolworths(?:\s+supermarket)?|woolies', 'Woolworths'),
    (r'(?i)coles(?:\s+supermarket)?', 'Coles'),
    (r'(?i)aldi(?:\s+store)?', 'Aldi'),
    (r'(?i)iga', 'IGA'),
    (r'(?i)nestle|nestlé|nestleau|nestleaust', 'Nestlé Australia'),
    (r'(?i)nespresso australia', 'Nespresso Australia'),
    
    # Restaurants and cafes
    (r'(?i)soul origin', 'Soul Origin'),
    (r'(?i)space kitchen', 'Space Kitchen'),
    (r'(?i)bean origin', 'Bean Origin'),
    (r'(?i)bliss and espresso macquarie', 'Bliss and Espresso Macquarie'),
    (r'(?i)sushi sushi', 'Sushi Sushi'),
    (r'(?i)tfc sushi', 'TFC Sushi'),
    (r'(?i)zambrero', 'Zambrero'),
    (r'(?i)the spence grocer', 'The Spence Grocer'),
    (r'(?i)mcdonalds|mcdonald\'s|maccas', 'McDonald\'s'),
    (r'(?i)millsandgrills', 'Mills and Grills'),
    (r'(?i)dickson taphouse', 'Dickson Taphouse'),
    (r'(?i)cafe|coffee', 'Cafe'),
    (r'(?i)restaurant|dining', 'Restaurant'),
    (r'(?i)pub|tavern', 'Pub'),
    (r'(?i)captains flat hote', 'Captains Flat Hotel'),
    
    # Pet Services
    (r'(?i)petpostaust', 'PetPost Australia'),
    (r'(?i)k9 and co adventure', 'K9 and Co Adventure'),
    (r'(?i)petstock pty ltd', 'Petstock Pty Ltd'),
    (r'(?i)petbarn', 'Petbarn'),
    (r'(?i)vet|veterinary', 'Veterinarian'),
    (r'(?i)pet warehouse', 'Pet Warehouse'),
    (r'(?i)pet circle', 'Pet Circle'),
    (r'(?i)pet shop', 'Pet Shop'),
    
    # Transport
    (r'(?i)uber', 'Uber'),
    (r'(?i)taxi|cab', 'Taxi'),
    (r'(?i)translink|go card', 'Public Transport'),
    (r'(?i)transport dickson', 'Transport Dickson'),
    
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
    (r'(?i)belconnen chiro', 'Belconnen Chiropractor'),
    (r'(?i)specsavers', 'Specsavers'),
    
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
    
    # Education
    (r'(?i)miles franklin', 'Miles Franklin'),
    (r'(?i)bounce holdings', 'Bounce Holdings'),
    (r'(?i)melba tennis club', 'Melba Tennis Club'),
    (r'(?i)on the line tennis melba', 'On The Line Tennis Melba'),
    (r'(?i)school|college|university|tafe', 'Educational Institution'),
    
    # Department stores
    (r'(?i)harris scarfe', 'Harris Scarfe'),
    (r'(?i)best and less', 'Best and Less'),
    (r'(?i)smiggle pty ltd', 'Smiggle'),
    (r'(?i)canberra southern yarralumla', 'Canberra Southern Yarralumla'),
    (r'(?i)rocksalt', 'Rocksalt'),
    (r'(?i)via dolce canberra', 'Via Dolce Canberra'),
    
    # Generic patterns (should be last)
    (r'(?i)supermarket', 'Generic Supermarket'),
]

# Default transaction categories and their keywords
DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    'Groceries': ['woolworths', 'coles', 'aldi', 'iga', 'supermarket', 'foodworks', 'nestle', 'nestlé', 'nestleau', 'nespresso australia', 'supa express'],
    'Dining': ['restaurant', 'cafe', 'coffee', 'pub', 'tavern', 'bistro', 'soul origin', 'space kitchen', 'bean origin', 'bliss and espresso macquarie', 'sushi sushi', 'tfc sushi', 'zambrero', 'the spence grocer', 'mcdonalds', 'mcdonald\'s', 'maccas', 'millsandgrills', 'mills and grills', 'dickson taphouse', 'canberra southern yarralumla', 'rocksalt', 'via dolce canberra', 'captains flat hotel', 'bravo vino pty ltd'],
    'Transport': ['uber', 'taxi', 'cab', 'translink', 'go card', 'train', 'bus', 'parking', 'car park', 'parking fee', 'parking ticket', 'parking meter', 'parking permit', 'transport dickson'],
    'Entertainment': ['netflix', 'spotify', 'cinema', 'movie', 'theatre', 'ticketek', 'hoyts'],
    'Shopping': ['amazon', 'ebay', 'target', 'kmart', 'big w', 'david jones', 'myer', 'harris scarfe', 'best and less', 'smiggle', 'bunnings', 'mitre 10', 'home hardware', 'hardware store', 'hardware shop', 'jb hi-fi', 'jb hifi', 'jbhifi', 'jb hi fi', 'harvey norman', 'harveynorman', 'the good guys', 'good guys', 'officeworks'],
    'Utilities': ['origin energy', 'agl', 'telstra', 'optus', 'belong', 'electricity', 'water', 'gas'],
    'Health': ['pharmacy', 'chemist', 'medical', 'doctor', 'dental', 'amcal', 'endota spa', 'www.endota.com.au', 'belconnen chiro', 'belconnen chiropractor', 'specsavers'],
    'Education': ['university', 'school', 'college', 'tafe', 'course', 'miles franklin', 'bounce holdings', 'educational institution', 'melba tennis club', 'on the line tennis melba'],
    'Insurance': ['insurance', 'budget direct', 'nrma', 'racq', 'racv', 'aami'],
    'Fuel': ['7-eleven', '7 eleven', '-eleven', 'bp', 'shell', 'caltex', 'united petroleum', 'petrol', 'service station'],
    'Holiday': ['hotel', 'motel', 'resort', 'accor', 'vacation', 'holiday', 'accommodation'],
    'Pet Expenses': ['petpostaust', 'k9 and co adventure', 'petstock pty ltd', 'petbarn', 'vet', 'veterinary', 'pet warehouse', 'pet circle', 'pet shop', 'pet', 'animal', 'pet care', 'pet supplies', 'animal hospital', 'grooming', 'pet food', 'pet accessories', 'pet medication'],
    'Other': []  # Default category
}

def load_custom_config():
    """Load custom merchant patterns and categories from config file if available."""
    config_path = os.path.join(os.path.dirname(__file__), 'transaction_config.json')
    print(f"Loading configuration from: {config_path}")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print("Successfully loaded configuration file")
                
            # Validate configuration against schema
            try:
                validate(instance=config, schema=CONFIG_SCHEMA)
                print("Configuration validation successful")
            except ValidationError as e:
                print(f"Warning: Invalid configuration format: {e}")
                return DEFAULT_MERCHANT_PATTERNS, DEFAULT_CATEGORIES
                
            # Convert JSON format to the expected tuple/list format
            merchant_patterns = [(item['pattern'], item['normalized']) for item in config.get('merchant_patterns', [])]
            categories = config.get('categories', {})
            print(f"Loaded {len(merchant_patterns)} merchant patterns and {len(categories)} categories")
            
            return merchant_patterns, categories
        except Exception as e:
            print(f"Warning: Could not load custom configuration: {e}")
            return DEFAULT_MERCHANT_PATTERNS, DEFAULT_CATEGORIES
    else:
        print("Configuration file not found, using defaults")
        # Create a default config file if it doesn't exist
        create_default_config(config_path)
        return DEFAULT_MERCHANT_PATTERNS, DEFAULT_CATEGORIES

def create_default_config(config_path):
    """Create a default configuration file."""
    config = {
        'merchant_patterns': [
            {'pattern': pattern, 'normalized': normalized} 
            for pattern, normalized in DEFAULT_MERCHANT_PATTERNS
        ],
        'categories': DEFAULT_CATEGORIES
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created default configuration file at {config_path}")
    except Exception as e:
        print(f"Warning: Could not create default configuration file: {e}")

# Load configurations
MERCHANT_PATTERNS, CATEGORIES = load_custom_config()

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
    
    # Try to match specific patterns first
    for pattern, normalized in MERCHANT_PATTERNS:
        if re.search(pattern, description, re.IGNORECASE):
            return normalized
    
    # If no specific pattern matches, return the original description
    return description

def categorize_transaction(description: str) -> str:
    """
    Categorize a transaction based on its description.
    
    Args:
        description (str): Transaction description
        
    Returns:
        str: Transaction category
    """
    # Remove Square payment prefix if present
    description = re.sub(r'^SQ \*', '', description)
    
    # Remove PayPal payment prefix if present
    description = re.sub(r'^PAYPAL \*', '', description)
    
    # First try to match based on normalized merchant name
    normalized = normalize_merchant(description)
    
    # Then try to match based on keywords
    for category, keywords in CATEGORIES.items():
        if any(re.search(rf'(?i){re.escape(keyword)}', description) for keyword in keywords):
            return category
    
    return 'Other'

def validate_config_file(config_path: str = None) -> bool:
    """
    Validate the configuration file against the schema.
    
    Args:
        config_path (str, optional): Path to the configuration file.
            If None, uses the default path in the script's directory.
            
    Returns:
        bool: True if the configuration is valid, False otherwise.
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'transaction_config.json')
    
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}")
        return False
        
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        try:
            validate(instance=config, schema=CONFIG_SCHEMA)
            print("Configuration file is valid.")
            return True
        except ValidationError as e:
            print(f"Error: Invalid configuration format: {e}")
            return False
    except Exception as e:
        print(f"Error: Could not read configuration file: {e}")
        return False 