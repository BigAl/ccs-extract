"""
Transaction Rules Engine for custom categorization.

This module provides functionality for defining and applying custom rules
to categorize transactions based on user-defined patterns and conditions.
"""

import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import json
from datetime import datetime

@dataclass
class TransactionRule:
    """Represents a single transaction categorization rule."""
    name: str
    pattern: str
    category: str
    priority: int = 0
    description: Optional[str] = None
    amount_condition: Optional[Dict[str, Union[float, str]]] = None
    date_condition: Optional[Dict[str, str]] = None
    is_regex: bool = True

class TransactionRulesEngine:
    """Engine for applying custom transaction categorization rules."""
    
    def __init__(self, rules_file: Optional[str] = None):
        """Initialize the rules engine.
        
        Args:
            rules_file: Path to JSON file containing rules configuration
        """
        self.rules: List[TransactionRule] = []
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str) -> None:
        """Load rules from a JSON configuration file.
        
        Args:
            rules_file: Path to JSON file containing rules
        """
        try:
            with open(rules_file, 'r') as f:
                rules_data = json.load(f)
                self.rules = [self._parse_rule(rule) for rule in rules_data]
                # Sort rules by priority (higher priority first)
                self.rules.sort(key=lambda x: x.priority, reverse=True)
        except Exception as e:
            raise ValueError(f"Failed to load rules from {rules_file}: {str(e)}")
    
    def _parse_rule(self, rule_data: Dict) -> TransactionRule:
        """Parse a single rule from dictionary data.
        
        Args:
            rule_data: Dictionary containing rule configuration
            
        Returns:
            TransactionRule object
        """
        return TransactionRule(
            name=rule_data.get('name', ''),
            pattern=rule_data.get('pattern', ''),
            category=rule_data.get('category', 'Other'),
            priority=rule_data.get('priority', 0),
            description=rule_data.get('description'),
            amount_condition=rule_data.get('amount_condition'),
            date_condition=rule_data.get('date_condition'),
            is_regex=rule_data.get('is_regex', True)
        )
    
    def add_rule(self, rule: TransactionRule) -> None:
        """Add a single rule to the engine.
        
        Args:
            rule: TransactionRule object to add
        """
        self.rules.append(rule)
        # Re-sort rules by priority
        self.rules.sort(key=lambda x: x.priority, reverse=True)
    
    def _check_amount_condition(self, amount: float, condition: Dict[str, Union[float, str]]) -> bool:
        """Check if an amount meets the specified condition.
        
        Args:
            amount: Transaction amount to check
            condition: Dictionary containing amount condition
            
        Returns:
            True if condition is met, False otherwise
        """
        if not condition:
            return True
            
        operator = condition.get('operator', '==')
        value = float(condition.get('value', 0))
        
        if operator == '==':
            return amount == value
        elif operator == '>':
            return amount > value
        elif operator == '>=':
            return amount >= value
        elif operator == '<':
            return amount < value
        elif operator == '<=':
            return amount <= value
        elif operator == '!=':
            return amount != value
        else:
            return False
    
    def _check_date_condition(self, date: datetime, condition: Dict[str, str]) -> bool:
        """Check if a date meets the specified condition.
        
        Args:
            date: Transaction date to check
            condition: Dictionary containing date condition
            
        Returns:
            True if condition is met, False otherwise
        """
        if not condition:
            return True
            
        operator = condition.get('operator', '==')
        value = condition.get('value', '')
        
        try:
            target_date = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return False
            
        if operator == '==':
            return date.date() == target_date.date()
        elif operator == '>':
            return date.date() > target_date.date()
        elif operator == '>=':
            return date.date() >= target_date.date()
        elif operator == '<':
            return date.date() < target_date.date()
        elif operator == '<=':
            return date.date() <= target_date.date()
        else:
            return False
    
    def apply_rules(self, description: str, amount: float, date: datetime) -> Optional[str]:
        """Apply rules to a transaction and return the matching category.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            date: Transaction date
            
        Returns:
            Category name if a rule matches, None otherwise
        """
        for rule in self.rules:
            # Check pattern match
            if rule.is_regex:
                if not re.search(rule.pattern, description, re.IGNORECASE):
                    continue
            else:
                if rule.pattern.lower() not in description.lower():
                    continue
            
            # Check amount condition
            if not self._check_amount_condition(amount, rule.amount_condition):
                continue
                
            # Check date condition
            if not self._check_date_condition(date, rule.date_condition):
                continue
                
            return rule.category
        
        return None 