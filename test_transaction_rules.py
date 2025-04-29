"""Tests for the transaction rules engine."""

import pytest
from datetime import datetime
from transaction_rules import TransactionRule, TransactionRulesEngine

@pytest.fixture
def sample_rules():
    """Create a sample rules engine with test rules."""
    engine = TransactionRulesEngine()
    
    # Add test rules
    engine.add_rule(TransactionRule(
        name="Test Groceries",
        pattern="COLES|WOOLWORTHS",
        category="Groceries",
        priority=1
    ))
    
    engine.add_rule(TransactionRule(
        name="High Value Groceries",
        pattern="COLES|WOOLWORTHS",
        category="Special Groceries",
        priority=2,
        amount_condition={"operator": ">=", "value": 100.0}
    ))
    
    engine.add_rule(TransactionRule(
        name="Date Specific",
        pattern="TEST",
        category="Special",
        priority=1,
        date_condition={"operator": "==", "value": "2024-01-01"}
    ))
    
    return engine

def test_basic_rule_matching(sample_rules):
    """Test basic rule matching functionality."""
    # Test simple pattern matching
    category = sample_rules.apply_rules(
        "COLES SUPERMARKET",
        50.0,
        datetime.now()
    )
    assert category == "Groceries"
    
    # Test non-matching pattern
    category = sample_rules.apply_rules(
        "UNKNOWN STORE",
        50.0,
        datetime.now()
    )
    assert category is None

def test_amount_condition(sample_rules):
    """Test amount-based rule conditions."""
    # Test high value condition
    category = sample_rules.apply_rules(
        "COLES SUPERMARKET",
        150.0,
        datetime.now()
    )
    assert category == "Special Groceries"
    
    # Test regular value
    category = sample_rules.apply_rules(
        "COLES SUPERMARKET",
        50.0,
        datetime.now()
    )
    assert category == "Groceries"

def test_date_condition(sample_rules):
    """Test date-based rule conditions."""
    # Test matching date
    category = sample_rules.apply_rules(
        "TEST TRANSACTION",
        50.0,
        datetime(2024, 1, 1)
    )
    assert category == "Special"
    
    # Test non-matching date
    category = sample_rules.apply_rules(
        "TEST TRANSACTION",
        50.0,
        datetime(2024, 1, 2)
    )
    assert category is None

def test_rule_priority(sample_rules):
    """Test that higher priority rules take precedence."""
    # Both rules match, but higher priority should win
    category = sample_rules.apply_rules(
        "COLES SUPERMARKET",
        150.0,
        datetime.now()
    )
    assert category == "Special Groceries"

def test_load_rules_from_file(tmp_path):
    """Test loading rules from a JSON file."""
    # Create a temporary rules file
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("""
    [
        {
            "name": "Test Rule",
            "pattern": "TEST",
            "category": "Test Category",
            "priority": 1
        }
    ]
    """)
    
    # Load rules from file
    engine = TransactionRulesEngine(str(rules_file))
    
    # Test rule matching
    category = engine.apply_rules(
        "TEST TRANSACTION",
        50.0,
        datetime.now()
    )
    assert category == "Test Category"

def test_invalid_rules_file(tmp_path):
    """Test handling of invalid rules file."""
    # Create an invalid JSON file
    rules_file = tmp_path / "invalid.json"
    rules_file.write_text("invalid json")
    
    # Attempt to load rules
    with pytest.raises(ValueError):
        TransactionRulesEngine(str(rules_file))

def test_non_regex_pattern():
    """Test non-regex pattern matching."""
    engine = TransactionRulesEngine()
    engine.add_rule(TransactionRule(
        name="Exact Match",
        pattern="EXACT MATCH",
        category="Test",
        priority=1,
        is_regex=False
    ))
    
    # Test exact match
    category = engine.apply_rules(
        "THIS IS AN EXACT MATCH TEST",
        50.0,
        datetime.now()
    )
    assert category == "Test"
    
    # Test partial match (should not match)
    category = engine.apply_rules(
        "EXACT",
        50.0,
        datetime.now()
    )
    assert category is None 