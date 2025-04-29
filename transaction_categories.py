"""
Transaction categorization and normalization rules for CCS-Extract.
"""

import re
import json
import os
import argparse
from typing import Dict, List, Tuple
from jsonschema import validate, ValidationError

from australian_merchants import STANDARD_MERCHANT_PATTERNS, STANDARD_CATEGORIES

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

def load_custom_config(config_file: str = None) -> Tuple[List[Tuple[str, str]], Dict[str, List[str]]]:
    """Load custom merchant patterns and categories from config file if available.
    
    Args:
        config_file: Path to the custom configuration file. If None, uses default path.
        
    Returns:
        Tuple containing:
        - List of (pattern, normalized) tuples for merchant patterns
        - Dictionary of categories and their keywords
        
    Raises:
        FileNotFoundError: If the config file does not exist
        json.JSONDecodeError: If the config file is not valid JSON
        ValidationError: If the config file does not match the required schema
    """
    if config_file is None:
        config_file = os.path.join(os.path.dirname(__file__), 'transaction_config.json')
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in configuration file: {e}", e.doc, e.pos)
    
    # Validate configuration against schema
    try:
        validate(instance=config, schema=CONFIG_SCHEMA)
    except ValidationError as e:
        raise ValidationError(f"Invalid configuration format: {e}")
    
    # Convert JSON format to the expected tuple/list format
    merchant_patterns = [(item['pattern'], item['normalized']) for item in config.get('merchant_patterns', [])]
    categories = config.get('categories', {})
    
    # Combine with standard patterns
    all_patterns = STANDARD_MERCHANT_PATTERNS + merchant_patterns
    all_categories = {**STANDARD_CATEGORIES, **categories}
    
    return all_patterns, all_categories

def create_default_config(config_path: str) -> None:
    """Create a default configuration file with empty custom patterns and categories."""
    config = {
        'merchant_patterns': [],
        'categories': {}
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created default configuration file at {config_path}")
    except Exception as e:
        print(f"Warning: Could not create default configuration file: {e}")

def normalize_merchant(description: str, patterns: List[Tuple[str, str]] = None) -> str:
    """
    Normalize merchant names in transaction descriptions.
    
    Args:
        description: Original transaction description
        patterns: List of (pattern, normalized) tuples to use for normalization.
                 If None, uses standard patterns.
        
    Returns:
        str: Normalized merchant name
    """
    if patterns is None:
        patterns = STANDARD_MERCHANT_PATTERNS
    
    # Remove Square payment prefix if present
    description = re.sub(r'^SQ \*', '', description)
    
    # Remove PayPal payment prefix if present
    description = re.sub(r'^PAYPAL \*', '', description)
    
    # Try to match specific patterns first
    for pattern, normalized in patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return normalized
    
    # If no specific pattern matches, return the original description
    return description

def categorize_transaction(description: str, categories: Dict[str, List[str]] = None) -> str:
    """
    Categorize a transaction based on its description.
    
    Args:
        description: Transaction description
        categories: Dictionary of categories and their keywords.
                   If None, uses standard categories.
        
    Returns:
        str: Transaction category
    """
    if categories is None:
        categories = STANDARD_CATEGORIES
    
    # Remove Square payment prefix if present
    description = re.sub(r'^SQ \*', '', description)
    
    # Remove PayPal payment prefix if present
    description = re.sub(r'^PAYPAL \*', '', description)
    
    # First try to match based on normalized merchant name
    normalized = normalize_merchant(description)
    
    # Then try to match based on keywords
    for category, keywords in categories.items():
        if any(re.search(rf'(?i){re.escape(keyword)}', description) for keyword in keywords):
            return category
    
    # If no match is found, return 'Other'
    return 'Other'

def validate_config_file(config_path: str = None) -> bool:
    """
    Validate the configuration file against the schema.
    
    Args:
        config_path: Path to the configuration file.
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

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Transaction categorization and normalization')
    parser.add_argument('--config', '-c', type=str, help='Path to custom configuration file')
    parser.add_argument('--validate', '-v', action='store_true', help='Validate configuration file')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    if args.validate:
        if args.config:
            validate_config_file(args.config)
        else:
            validate_config_file()
    else:
        # Load configuration
        patterns, categories = load_custom_config(args.config)
        
        # Example usage
        test_description = "SQ *Space Kitchen"
        normalized = normalize_merchant(test_description, patterns)
        category = categorize_transaction(test_description, categories)
        print(f"Description: {test_description}")
        print(f"Normalized: {normalized}")
        print(f"Category: {category}") 