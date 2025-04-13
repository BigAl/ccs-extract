"""
Tests for the credit card statement extractor.
"""

import os
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from ccs_extract import StatementExtractor
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
def extractor():
    """Create a StatementExtractor instance for testing."""
    return StatementExtractor(debug_mode=True)

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

@patch('ccs_extract.PdfReader')  # Updated to patch the correct import
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

def test_process_statement_default_output(extractor, tmp_path):
    """Test processing statement with default output path."""
    # Create a temporary PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement
        extractor.process_statement(str(pdf_path))
        
        # Check default output file was created
        default_output = tmp_path / "test.csv"
        assert default_output.exists()
        content = default_output.read_text()
        assert 'Transaction Date' in content
        assert 'GROCERY STORE' in content

def test_process_statement_custom_output(extractor, tmp_path):
    """Test processing statement with custom output path."""
    # Create a temporary PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    
    # Create custom output path
    custom_output = tmp_path / "custom.csv"
    
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement with custom output
        extractor.process_statement(str(pdf_path), output_path=str(custom_output))
        
        # Check custom output file was created
        assert custom_output.exists()
        content = custom_output.read_text()
        assert 'Transaction Date' in content
        assert 'GROCERY STORE' in content

def test_process_statement_debug_output(extractor, tmp_path):
    """Test processing statement with debug output."""
    # Create a temporary PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement
        extractor.process_statement(str(pdf_path))
        
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
    
    # Test restaurants and cafes
    assert normalize_merchant("CAFE EXPRESS") == "Cafe"
    assert normalize_merchant("RESTAURANT NAME") == "Restaurant"
    assert normalize_merchant("PUB AND GRILL") == "Pub"
    
    # Test transport
    assert normalize_merchant("UBER *TRIP") == "Uber"
    assert normalize_merchant("TAXI SERVICE") == "Taxi"
    assert normalize_merchant("TRANSLINK GO CARD") == "Public Transport"
    
    # Test online services
    assert normalize_merchant("NETFLIX.COM") == "Netflix"
    assert normalize_merchant("SPOTIFY PREMIUM") == "Spotify"
    assert normalize_merchant("AMAZON.COM") == "Amazon"
    
    # Test utilities
    assert normalize_merchant("ORIGIN ENERGY") == "Origin Energy"
    assert normalize_merchant("AGL ELECTRICITY") == "AGL"
    assert normalize_merchant("TELSTRA BILL") == "Telstra"
    
    # Test unknown merchant
    assert normalize_merchant("UNKNOWN STORE") == "UNKNOWN STORE"

def test_categorize_transaction():
    """Test transaction categorization."""
    # Test groceries
    assert categorize_transaction("WOOLWORTHS SUPERMARKET") == "Groceries"
    assert categorize_transaction("COLES") == "Groceries"
    assert categorize_transaction("ALDI") == "Groceries"
    
    # Test dining
    assert categorize_transaction("RESTAURANT NAME") == "Dining"
    assert categorize_transaction("CAFE EXPRESS") == "Dining"
    assert categorize_transaction("PUB AND GRILL") == "Dining"
    
    # Test transport
    assert categorize_transaction("UBER TRIP") == "Transport"
    assert categorize_transaction("TAXI SERVICE") == "Transport"
    assert categorize_transaction("TRANSLINK") == "Transport"
    
    # Test entertainment
    assert categorize_transaction("NETFLIX") == "Entertainment"
    assert categorize_transaction("SPOTIFY") == "Entertainment"
    assert categorize_transaction("CINEMA") == "Entertainment"
    
    # Test shopping
    assert categorize_transaction("AMAZON") == "Shopping"
    assert categorize_transaction("TARGET") == "Shopping"
    assert categorize_transaction("KMART") == "Shopping"
    
    # Test utilities
    assert categorize_transaction("ORIGIN ENERGY") == "Utilities"
    assert categorize_transaction("AGL") == "Utilities"
    assert categorize_transaction("TELSTRA") == "Utilities"
    
    # Test health
    assert categorize_transaction("PHARMACY") == "Health"
    assert categorize_transaction("CHEMIST") == "Health"
    assert categorize_transaction("MEDICAL CENTRE") == "Health"
    
    # Test education
    assert categorize_transaction("UNIVERSITY") == "Education"
    assert categorize_transaction("SCHOOL") == "Education"
    assert categorize_transaction("COLLEGE") == "Education"
    
    # Test insurance
    assert categorize_transaction("INSURANCE") == "Insurance"
    assert categorize_transaction("NRMA") == "Insurance"
    assert categorize_transaction("RACQ") == "Insurance"
    
    # Test unknown category
    assert categorize_transaction("UNKNOWN STORE") == "Other"

def test_clean_transactions_with_categorization(extractor, tmp_path):
    """Test transaction cleaning with categorization."""
    # Create a temporary PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')  # Write minimal PDF header
    
    # Mock the PDF reader
    with patch('ccs_extract.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_TRANSACTION_TEXT
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Process statement
        extractor.process_statement(str(pdf_path))
        
        # Check output file was created
        output_path = tmp_path / "test.csv"
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