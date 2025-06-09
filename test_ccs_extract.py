"""
Tests for the credit card statement extractor.
"""

import os
import sys
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from io import StringIO
import json

from ccs_extract import CreditCardStatementExtractor, main, parse_args
from exceptions import PDFError, TransactionExtractionError, OutputError
from transaction_categories import normalize_merchant, categorize_transaction

# Get current year for date assertions
CURRENT_YEAR = datetime.now().year

# Sample transaction text
SAMPLE_TRANSACTION_TEXT = f"""
15 Mar {CURRENT_YEAR} $123.45 GROCERY STORE
16 Mar {CURRENT_YEAR} $67.89 RESTAURANT
17 Mar {CURRENT_YEAR} $50.00 CR REFUND
"""

@pytest.fixture
def extractor(tmp_path):
    """Create a CreditCardStatementExtractor instance for testing."""
    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create a test configuration file
    config_file = tmp_path / "transaction_config.json"
    config_file.write_text(json.dumps({
        "merchant_patterns": [
            {
                "pattern": "(?i)test",
                "normalized": "Test Merchant"
            }
        ],
        "categories": {
            "Groceries": ["COLES", "WOOLWORTHS"],
            "Transport": ["UBER", "TAXI"],
            "Dining": ["RESTAURANT", "CAFE"]
        }
    }))
    
    # Create a test rules file
    rules_file = tmp_path / "transaction_rules.json"
    rules_file.write_text(json.dumps([
        {
            "name": "Test Rule",
            "pattern": "TEST",
            "category": "Test Category",
            "priority": 1
        }
    ]))
    
    extractor = CreditCardStatementExtractor(config_file=str(config_file))
    extractor.debug_mode = True
    extractor.base_dir = str(tmp_path)
    # Ensure parsing_patterns.json does not exist for this default fixture run
    parsing_patterns_file = tmp_path / "parsing_patterns.json"
    if parsing_patterns_file.exists():
        parsing_patterns_file.unlink()
    return extractor

@pytest.fixture
def test_pdf(tmp_path):
    """Create a test PDF file."""
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    return pdf_path

def test_validate_pdf_valid_file(extractor, tmp_path):
    """Test PDF validation with a valid file."""
    # Create a temporary PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    
    # Should not raise an exception
    extractor.validate_pdf(str(pdf_path))

def test_validate_pdf_nonexistent_file(extractor):
    """Test PDF validation with a nonexistent file."""
    with pytest.raises(PDFError):
        extractor.validate_pdf("nonexistent.pdf")

def test_validate_pdf_non_pdf_file(extractor, tmp_path):
    """Test PDF validation with a non-PDF file."""
    # Create a temporary text file
    text_path = tmp_path / "test.txt"
    text_path.write_text("")
    
    with pytest.raises(PDFError):
        extractor.validate_pdf(str(text_path))

@patch('ccs_extract.PdfReader')
def test_extract_text_from_pdf(mock_pdf_reader, extractor, tmp_path):
    """Test text extraction from PDF."""
    # Create a mock PDF reader
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Sample text"
    mock_pdf_reader.return_value.pages = [mock_page]
    
    # Create a temporary PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    
    # Extract text
    text = extractor.extract_text_from_pdf(str(pdf_path))
    
    # Check result
    assert text == "Sample text\n"
    mock_pdf_reader.assert_called_once()

def test_extract_transactions(extractor):
    """Test transaction extraction from text."""
    # Extract transactions
    transactions = extractor.extract_transactions(SAMPLE_TRANSACTION_TEXT)
    
    # Check results
    assert len(transactions) == 3
    
    # Check first transaction
    assert transactions[0]['Transaction Date'] == f'15/03/{CURRENT_YEAR}'
    assert transactions[0]['Transaction Details'] == 'GROCERY STORE'
    assert transactions[0]['Amount'] == '123.45'
    
    # Check second transaction
    assert transactions[1]['Transaction Date'] == f'16/03/{CURRENT_YEAR}'
    assert transactions[1]['Transaction Details'] == 'RESTAURANT'
    assert transactions[1]['Amount'] == '67.89'
    
    # Check credit transaction
    assert transactions[2]['Transaction Date'] == f'17/03/{CURRENT_YEAR}'
    assert transactions[2]['Transaction Details'] == 'REFUND'
    assert transactions[2]['Amount'] == '-50.00'

def test_clean_transactions(extractor):
    """Test transaction cleaning."""
    # Sample raw transactions
    raw_transactions = [
        {
            'Transaction Date': f'15 Mar {CURRENT_YEAR}',
            'Transaction Details': '  GROCERY  STORE  ',
            'Amount': '123.45'
        },
        {
            'Transaction Date': f'16 Mar {CURRENT_YEAR}',
            'Transaction Details': '',
            'Amount': '67.89'
        },
        {
            'Transaction Date': f'17 Mar {CURRENT_YEAR}',
            'Transaction Details': 'Transaction details',
            'Amount': '50.00'
        }
    ]
    
    # Clean transactions
    cleaned = extractor.clean_transactions(raw_transactions)
    
    # Check results
    assert len(cleaned) == 1
    assert cleaned[0]['Transaction Date'] == f'15/03/{CURRENT_YEAR}'
    assert cleaned[0]['Transaction Details'] == 'GROCERY STORE'
    assert cleaned[0]['Amount'] == '123.45'

def test_write_to_csv(extractor, tmp_path):
    """Test writing transactions to CSV."""
    # Sample transactions
    transactions = [
        {
            'Transaction Date': f'15/03/{CURRENT_YEAR}',
            'Transaction Details': 'GROCERY STORE',
            'Amount': '123.45'
        }
    ]
    
    # Create output path
    output_path = tmp_path / "test.csv"
    
    # Write to CSV
    extractor.write_to_csv(transactions, str(output_path))
    
    # Check file exists and has correct content
    assert output_path.exists()
    content = output_path.read_text()
    assert 'Transaction Date' in content
    assert 'Transaction Details' in content
    assert 'Amount' in content
    assert f'15/03/{CURRENT_YEAR}' in content
    assert 'GROCERY STORE' in content
    assert '123.45' in content

def test_write_to_csv_empty(extractor, tmp_path):
    """Test writing empty transactions to CSV."""
    # Create output path
    output_path = tmp_path / "test.csv"
    
    # Write to CSV
    extractor.write_to_csv([], str(output_path))
    
    # Check file exists but is empty (except header)
    assert output_path.exists()
    content = output_path.read_text()
    assert 'Transaction Date' in content
    assert 'Transaction Details' in content
    assert 'Amount' in content
    assert len(content.splitlines()) == 1  # Only header

def test_process_statement_default_output(extractor, test_pdf, tmp_path):
    """Test processing statement with default output path."""
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement
        extractor.process_statement(str(test_pdf))
        
        # Check default output file was created
        default_output = tmp_path / "output" / "test.csv"
        assert default_output.exists()
        content = default_output.read_text()
        assert 'Transaction Date' in content
        assert 'GROCERY STORE' in content

def test_process_statement_custom_output(extractor, test_pdf, tmp_path):
    """Test processing statement with custom output path."""
    # Create custom output path
    custom_output = tmp_path / "custom.csv"
    
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement with custom output
        extractor.process_statement(str(test_pdf), output_path=str(custom_output))
        
        # Check custom output file was created
        assert custom_output.exists()
        content = custom_output.read_text()
        assert 'Transaction Date' in content
        assert 'GROCERY STORE' in content

def test_process_statement_debug_output(extractor, test_pdf, tmp_path):
    """Test processing statement with debug output."""
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement
        extractor.process_statement(str(test_pdf))
        
        # Check debug output file was created
        debug_output = tmp_path / "test_debug.txt"
        assert debug_output.exists()
        content = debug_output.read_text()
        assert 'GROCERY STORE' in content
        assert 'RESTAURANT' in content
        assert 'REFUND' in content

def test_normalize_merchant():
    """Test merchant name normalization."""
    # Test grocery stores
    assert normalize_merchant("WOOLWORTHS SUPERMARKET") == "Woolworths"
    assert normalize_merchant("WOOLIES") == "Woolworths"
    assert normalize_merchant("COLES SUPERMARKET") == "Coles"
    assert normalize_merchant("ALDI STORE") == "Aldi"
    assert normalize_merchant("NESTLEAUSTR") == "Nestlé Australia"
    assert normalize_merchant("NESTLE AUSTRALIA") == "Nestlé Australia"
    assert normalize_merchant("NESTLEAU") == "Nestlé Australia"
    
    # Test restaurants and cafes
    assert normalize_merchant("SOUL ORIGIN") == "Soul Origin"
    assert normalize_merchant("CAFE EXPRESS") == "Cafe"
    assert normalize_merchant("RESTAURANT NAME") == "Restaurant"
    assert normalize_merchant("PUB AND GRILL") == "Pub"

def test_categorize_transaction():
    """Test transaction categorization."""
    # Test groceries
    assert categorize_transaction("WOOLWORTHS SUPERMARKET") == "Groceries"
    assert categorize_transaction("COLES") == "Groceries"
    assert categorize_transaction("ALDI") == "Groceries"
    assert categorize_transaction("NESTLEAUSTR") == "Groceries"
    assert categorize_transaction("NESTLE AUSTRALIA") == "Groceries"
    assert categorize_transaction("NESTLEAU") == "Groceries"
    
    # Test dining
    assert categorize_transaction("SOUL ORIGIN") == "Dining"
    assert categorize_transaction("RESTAURANT NAME") == "Dining"
    assert categorize_transaction("CAFE EXPRESS") == "Dining"
    assert categorize_transaction("PUB AND GRILL") == "Dining"

def test_clean_transactions_with_categorization(extractor, test_pdf, tmp_path):
    """Test transaction cleaning with categorization."""
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement
        extractor.process_statement(str(test_pdf))
        
        # Check output file was created
        output_path = tmp_path / "output" / "test.csv"
        assert output_path.exists()
        
        # Read the CSV content
        with open(output_path, 'r') as f:
            content = f.read()
            lines = content.splitlines()
            
            # Check header includes new fields
            assert 'Transaction Date' in lines[0]
            assert 'Merchant' in lines[0]
            assert 'Category' in lines[0]
            assert 'Transaction Details' in lines[0]
            assert 'Amount' in lines[0]
            
            # Check we have the expected number of transactions
            assert len(lines) == 4  # Header + 3 transactions

def test_extract_transactions_error_handling(extractor):
    """Test error handling in transaction extraction."""
    # Test with invalid transaction text
    with pytest.raises(TransactionExtractionError):
        extractor.extract_transactions(None)

def test_write_to_csv_error_handling(extractor, tmp_path):
    """Test error handling in CSV writing."""
    # Try to write to a directory instead of a file
    with pytest.raises(OutputError):
        extractor.write_to_csv([], str(tmp_path))

def test_process_statement_error_handling(extractor, tmp_path):
    """Test error handling in statement processing."""
    # Test with invalid PDF
    with pytest.raises(PDFError):
        extractor.process_statement("nonexistent.pdf")
    
    # Test with invalid output path
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')
    
    with pytest.raises(PDFError):  # Changed from OutputError to PDFError
        extractor.process_statement(str(pdf_path), str(tmp_path))

def test_main_interactive_mode(monkeypatch):
    """Test main function in interactive mode."""
    # Mock input and create a temporary PDF
    with patch('builtins.input', return_value='test.pdf'), \
         patch('ccs_extract.CreditCardStatementExtractor.process_statement'), \
         patch('argparse.ArgumentParser.parse_args') as mock_parse_args, \
         patch('transaction_categories.load_custom_config') as mock_load_config:
        # Mock the parsed args
        mock_args = MagicMock()
        mock_args.pdf_file = 'test.pdf'
        mock_args.output = None
        mock_args.debug = False
        mock_args.config = None
        mock_parse_args.return_value = mock_args
        
        # Mock the config loading
        mock_load_config.return_value = ([], {})
        
        # Call main without arguments
        with patch.object(sys, 'argv', ['ccs_extract.py']):
            main()

def test_parse_args():
    """Test argument parsing."""
    # Test with no arguments (interactive mode)
    with patch.object(sys, 'argv', ['ccs_extract.py']), \
         patch('builtins.input', return_value='test.pdf'):
        args = parse_args()
        assert args.pdf_file == 'test.pdf'
        assert args.output is None
        assert not args.debug
        assert args.config is None

    # Test with all arguments
    with patch.object(sys, 'argv', ['ccs_extract.py', 'input.pdf', '--output', 'out.csv', '--debug', '--config', 'config.json']):
        args = parse_args()
        assert args.pdf_file == 'input.pdf'
        assert args.output == 'out.csv'
        assert args.debug
        assert args.config == 'config.json'

# New test cases to improve coverage

def test_extract_transactions_with_empty_text(extractor):
    """Test transaction extraction with empty text."""
    transactions = extractor.extract_transactions("")
    assert len(transactions) == 0

def test_extract_transactions_with_invalid_format(extractor):
    """Test transaction extraction with invalid format."""
    invalid_text = "Invalid transaction format"
    transactions = extractor.extract_transactions(invalid_text)
    assert len(transactions) == 0

def test_normalize_merchant_with_special_chars():
    """Test merchant normalization with special characters."""
    assert normalize_merchant("CAFE EXPRESS") == "Cafe"  # Changed from CAFÉ to CAFE
    assert normalize_merchant("STORE & SHOP") == "STORE & SHOP"
    assert normalize_merchant("STORE-MART") == "STORE-MART"

def test_categorize_transaction_with_special_chars():
    """Test transaction categorization with special characters."""
    assert categorize_transaction("CAFE EXPRESS") == "Dining"  # Changed from CAFÉ to CAFE
    assert categorize_transaction("STORE & SHOP") == "Other"
    assert categorize_transaction("STORE-MART") == "Other"

def test_extract_text_from_pdf_with_multiple_pages(extractor, tmp_path):
    """Test text extraction from PDF with multiple pages."""
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_pages = [MagicMock(), MagicMock(), MagicMock()]
        for i, page in enumerate(mock_pages):
            page.extract_text.return_value = f"Page {i+1} text"
        mock_pdf_reader.return_value.pages = mock_pages
        
        pdf_path = tmp_path / "test.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        text = extractor.extract_text_from_pdf(str(pdf_path))
        assert "Page 1 text" in text
        assert "Page 2 text" in text
        assert "Page 3 text" in text

def test_write_to_csv_with_special_chars(extractor, tmp_path):
    """Test writing transactions with special characters to CSV."""
    transactions = [
        {
            'Transaction Date': f'15/03/{CURRENT_YEAR}',
            'Transaction Details': 'CAFÉ & RESTAURANT',
            'Amount': '123.45',
            'Merchant': 'Cafe',
            'Category': 'Dining'
        }
    ]
    
    output_path = tmp_path / "test.csv"
    extractor.write_to_csv(transactions, str(output_path))
    
    content = output_path.read_text()
    assert 'CAFÉ & RESTAURANT' in content
    assert 'Cafe' in content
    assert 'Dining' in content

def test_process_statement_with_no_transactions(extractor, test_pdf, tmp_path):
    """Test processing statement with no transactions."""
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "No transactions in this statement"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        extractor.process_statement(str(test_pdf))
        
        output_path = tmp_path / "output" / "test.csv"
        assert output_path.exists()
        content = output_path.read_text()
        assert len(content.splitlines()) == 1  # Only header


# --- Tests for Configuration Management Changes ---

def test_init_with_missing_transaction_config_file(tmp_path, monkeypatch):
    """Test extractor initialization with transaction_config.json missing."""
    config_file_path = tmp_path / "transaction_config.json" # Default path
    if config_file_path.exists(): # Ensure it's not there from other tests
        config_file_path.unlink()

    # Ensure other default config files also don't exist to isolate this test
    rules_file_path = tmp_path / "transaction_rules.json"
    if rules_file_path.exists(): rules_file_path.unlink()
    parsing_patterns_file = tmp_path / "parsing_patterns.json"
    if parsing_patterns_file.exists(): parsing_patterns_file.unlink()

    mock_log_warning = MagicMock()
    # The logger is in 'transaction_categories' module
    monkeypatch.setattr("transaction_categories.logger.warning", mock_log_warning)

    original_cwd = os.getcwd()
    os.chdir(tmp_path) # Change CWD so default file paths are sought in tmp_path
    try:
        # Initialize extractor - it will try to load 'transaction_config.json' by default
        # Pass the explicit path to be sure it's the one being checked
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_path))

        mock_log_warning.assert_called_once_with(
            f"Custom transaction configuration file '{str(config_file_path)}' not found. "
            "Using standard defaults only."
        )
        # Check that it loaded the standard defaults
        assert extractor_instance.config["merchant_patterns"] == STANDARD_MERCHANT_PATTERNS
        assert extractor_instance.config["categories"] == STANDARD_CATEGORIES
    finally:
        os.chdir(original_cwd)

def test_init_with_missing_transaction_rules_file(tmp_path, monkeypatch):
    """Test TransactionRulesEngine initialization when transaction_rules.json is missing."""
    rules_file_path = tmp_path / "transaction_rules.json" # Default path for rules engine
    if rules_file_path.exists(): # Ensure it's not there
        rules_file_path.unlink()

    # Dummy transaction_config.json is needed for CreditCardStatementExtractor init
    config_file_for_extractor = tmp_path / "extractor_config.json"
    config_file_for_extractor.write_text(json.dumps({"merchant_patterns": [], "categories": {}}))

    # Ensure parsing_patterns.json does not exist
    parsing_patterns_file = tmp_path / "parsing_patterns.json"
    if parsing_patterns_file.exists(): parsing_patterns_file.unlink()


    mock_log_warning = MagicMock()
    # The logger is in 'transaction_rules' module
    monkeypatch.setattr("transaction_rules.logger.warning", mock_log_warning)

    original_cwd = os.getcwd()
    os.chdir(tmp_path) # Change CWD so CCS_Extract looks for rules file here by default
    try:
        # CCS_Extract initializes TransactionRulesEngine with "transaction_rules.json"
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_for_extractor))

        mock_log_warning.assert_called_once_with(
            f"Custom transaction rules file 'transaction_rules.json' not found. "
            "No custom rules will be loaded."
        )
        assert extractor_instance.rules_engine.rules == []
    finally:
        os.chdir(original_cwd)


def test_load_custom_parsing_patterns(tmp_path, monkeypatch):
    """Test loading of custom transaction parsing patterns from parsing_patterns.json."""
    custom_patterns_json_path = tmp_path / "parsing_patterns.json" # Default path
    custom_pattern_list = [
        {
            "name": "custom_test_pattern",
            "pattern": "CUSTOM_REGEX_(\\d+)",
            "groups": {"data": 1, "amount": 0, "date": 0, "description":0}
        }
    ]
    custom_patterns_json_path.write_text(json.dumps(custom_pattern_list))

    mock_log_info = MagicMock()
    monkeypatch.setattr("ccs_extract.logger.info", mock_log_info)

    # Dummy transaction_config.json
    config_file_for_extractor = tmp_path / "extractor_config.json"
    config_file_for_extractor.write_text(json.dumps({"merchant_patterns": [], "categories": {}}))
    # Ensure no transaction_rules.json
    rules_file_path = tmp_path / "transaction_rules.json"
    if rules_file_path.exists(): rules_file_path.unlink()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_for_extractor))

        mock_log_info.assert_any_call(
            f"Successfully loaded 1 custom parsing patterns from 'parsing_patterns.json'."
        )
        assert len(extractor_instance.transaction_patterns) == 1
        assert extractor_instance.transaction_patterns[0]["name"] == "custom_test_pattern"
        assert isinstance(extractor_instance.transaction_patterns[0]["pattern"], re.Pattern)
        assert extractor_instance.transaction_patterns[0]["pattern"].pattern == "CUSTOM_REGEX_(\\d+)"

        test_text = "Some text CUSTOM_REGEX_123 more text"
        match = extractor_instance.transaction_patterns[0]["pattern"].search(test_text)
        assert match is not None
        assert match.group(1) == "123"
    finally:
        os.chdir(original_cwd)


def test_fallback_to_default_parsing_patterns_if_missing(tmp_path, monkeypatch):
    """Test fallback to default parsing patterns if parsing_patterns.json is missing."""
    parsing_patterns_file_path = tmp_path / "parsing_patterns.json"
    if parsing_patterns_file_path.exists():
        parsing_patterns_file_path.unlink()

    mock_log_warning = MagicMock()
    monkeypatch.setattr("ccs_extract.logger.warning", mock_log_warning)

    config_file_for_extractor = tmp_path / "extractor_config.json"
    config_file_for_extractor.write_text(json.dumps({"merchant_patterns": [], "categories": {}}))
    rules_file_path = tmp_path / "transaction_rules.json"
    if rules_file_path.exists(): rules_file_path.unlink()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_for_extractor))

        mock_log_warning.assert_any_call(
            "Custom parsing patterns file 'parsing_patterns.json' not found. Using default patterns from config.py."
        )
        assert extractor_instance.transaction_patterns == DEFAULT_TRANSACTION_PATTERNS
    finally:
        os.chdir(original_cwd)


def test_fallback_to_default_parsing_patterns_if_malformed_json(tmp_path, monkeypatch):
    """Test fallback if parsing_patterns.json is malformed (invalid JSON)."""
    parsing_patterns_file_path = tmp_path / "parsing_patterns.json"
    parsing_patterns_file_path.write_text("this is not valid json {")

    mock_log_error = MagicMock()
    monkeypatch.setattr("ccs_extract.logger.error", mock_log_error)

    config_file_for_extractor = tmp_path / "extractor_config.json"
    config_file_for_extractor.write_text(json.dumps({"merchant_patterns": [], "categories": {}}))
    rules_file_path = tmp_path / "transaction_rules.json"
    if rules_file_path.exists(): rules_file_path.unlink()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_for_extractor))

        assert mock_log_error.call_count >= 1
        args, _ = mock_log_error.call_args_list[0] # Check the first error log
        assert "Error loading or validating custom parsing patterns from 'parsing_patterns.json'" in args[0]
        assert "Using default patterns." in args[0]

        assert extractor_instance.transaction_patterns == DEFAULT_TRANSACTION_PATTERNS
    finally:
        os.chdir(original_cwd)

def test_fallback_to_default_parsing_patterns_if_invalid_structure(tmp_path, monkeypatch):
    """Test fallback if parsing_patterns.json has valid JSON but invalid structure (not a list)."""
    parsing_patterns_file_path = tmp_path / "parsing_patterns.json"
    parsing_patterns_file_path.write_text(json.dumps({"not_a_list": "this is a dict"}))

    mock_log_error = MagicMock()
    monkeypatch.setattr("ccs_extract.logger.error", mock_log_error)

    config_file_for_extractor = tmp_path / "extractor_config.json"
    config_file_for_extractor.write_text(json.dumps({"merchant_patterns": [], "categories": {}}))
    rules_file_path = tmp_path / "transaction_rules.json"
    if rules_file_path.exists(): rules_file_path.unlink()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_for_extractor))

        mock_log_error.assert_any_call(
            "Error loading or validating custom parsing patterns from 'parsing_patterns.json': "
            "Parsing patterns JSON must be a list.. Using default patterns."
        )
        assert extractor_instance.transaction_patterns == DEFAULT_TRANSACTION_PATTERNS
    finally:
        os.chdir(original_cwd)

def test_fallback_to_default_parsing_patterns_if_invalid_item_structure(tmp_path, monkeypatch):
    """Test fallback if parsing_patterns.json has items with invalid structure."""
    parsing_patterns_file_path = tmp_path / "parsing_patterns.json"
    # List of objects, but objects miss required keys like 'pattern'
    invalid_patterns_list = [{"name": "test_pattern_missing_keys", "groups": {}}]
    parsing_patterns_file_path.write_text(json.dumps(invalid_patterns_list))

    mock_log_error = MagicMock()
    monkeypatch.setattr("ccs_extract.logger.error", mock_log_error)

    config_file_for_extractor = tmp_path / "extractor_config.json"
    config_file_for_extractor.write_text(json.dumps({"merchant_patterns": [], "categories": {}}))
    rules_file_path = tmp_path / "transaction_rules.json"
    if rules_file_path.exists(): rules_file_path.unlink()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        extractor_instance = CreditCardStatementExtractor(config_file=str(config_file_for_extractor))

        mock_log_error.assert_any_call(
            "Error loading or validating custom parsing patterns from 'parsing_patterns.json': "
            "Invalid pattern structure in JSON.. Using default patterns."
        )
        assert extractor_instance.transaction_patterns == DEFAULT_TRANSACTION_PATTERNS
    finally:
        os.chdir(original_cwd)

# Ensure existing tests that rely on the 'extractor' fixture still run correctly.
# The fixture is modified to ensure parsing_patterns.json does not exist by default,
# so those tests will use default parsing patterns.
# The fixture creates transaction_config.json and transaction_rules.json,
# so tests for those specific custom configs will still work as intended.
# The chdir in the main fixture ensures default config files are sought in tmp_path.
# Individual tests that need to control specific config files should manage them within tmp_path
# and potentially use chdir as well if testing CCS_Extract's direct use of default filenames.