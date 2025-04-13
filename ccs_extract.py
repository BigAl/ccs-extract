"""
CCS-Extract

A Python utility for extracting transaction data from credit card statement PDFs
and converting them to CSV format.
"""

import re
import os
import sys
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Any

from pypdf import PdfReader
from tqdm import tqdm

# Import our modules
try:
    from config import (
        DATE_FORMATS,
        TRANSACTION_PATTERNS,
        CSV_SETTINGS,
        DEBUG_SETTINGS,
        FILE_SETTINGS
    )
    from logger import setup_logger
    from exceptions import (
        StatementExtractorError,
        PDFError,
        TransactionExtractionError,
        ValidationError,
        OutputError
    )
except ImportError:
    # Fallback to default values if modules are not available
    DATE_FORMATS = {
        'input': '%d %b %Y',  # Updated to include year
        'output': '%d/%m/%Y'
    }
    TRANSACTION_PATTERNS = [
        {
            'name': 'standard',
            'pattern': re.compile(r'(\d{1,2} [A-Za-z]{3} \d{4}) \$([\d,.]+)(.+)'),  # Updated to include year
            'groups': {
                'date': 1,
                'amount': 2,
                'description': 3
            }
        }
    ]
    CSV_SETTINGS = {
        'fieldnames': ['Transaction Date', 'Transaction Details', 'Amount'],
        'delimiter': ',',
        'quotechar': '"',
        'quoting': 'QUOTE_MINIMAL'
    }
    DEBUG_SETTINGS = {
        'sample_text_length': 500,
        'page_separator': '--- PAGE {} ---\n'
    }
    FILE_SETTINGS = {
        'encoding': 'utf-8',
        'output_suffix': '_transactions.csv',
        'debug_suffix': '_debug.txt'
    }
    
    # Simple logging setup if logger module is not available
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    setup_logger = lambda name: logging.getLogger(name)
    
    # Simple exception classes if exceptions module is not available
    class StatementExtractorError(Exception): pass
    class PDFError(StatementExtractorError): pass
    class TransactionExtractionError(StatementExtractorError): pass
    class ValidationError(StatementExtractorError): pass
    class OutputError(StatementExtractorError): pass

# Set up logger
logger = setup_logger(__name__)

class StatementExtractor:
    """Main class for extracting transactions from credit card statements."""
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the statement extractor.
        
        Args:
            debug_mode (bool): Whether to run in debug mode
        """
        self.debug_mode = debug_mode
        self.logger = logger
        self.current_year = datetime.now().year
        self.statement_text = ""
    
    def validate_pdf(self, pdf_path: str) -> None:
        """
        Validate that the file exists and is a PDF.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Raises:
            PDFError: If the file doesn't exist or isn't a PDF
        """
        if not os.path.exists(pdf_path):
            raise PDFError(f"File not found: {pdf_path}")
        
        if not pdf_path.lower().endswith('.pdf'):
            raise PDFError(f"File is not a PDF: {pdf_path}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text from the PDF
            
        Raises:
            PDFError: If there's an error reading the PDF
        """
        try:
            self.logger.info(f"Extracting text from {pdf_path}")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                # Extract text from all pages with progress bar
                full_text = ""
                for page_num in tqdm(range(len(pdf_reader.pages)), 
                                   desc="Processing pages",
                                   disable=not self.debug_mode):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    full_text += page_text + "\n"
                    
                    if self.debug_mode:
                        self.logger.debug(f"Page {page_num+1} sample: {page_text[:DEBUG_SETTINGS['sample_text_length']]}")
                
                return full_text
        except Exception as e:
            raise PDFError(f"Error reading PDF: {str(e)}")
    
    def extract_transactions(self, text: str) -> List[Dict[str, str]]:
        """
        Extract transactions from text using configured patterns.
        
        Args:
            text (str): Text to extract transactions from
            
        Returns:
            List[Dict[str, str]]: List of extracted transactions
            
        Raises:
            TransactionExtractionError: If there's an error extracting transactions
        """
        transactions = []
        
        try:
            # Process each line to find transactions
            for line in text.split('\n'):
                # Try each configured pattern
                for pattern_config in TRANSACTION_PATTERNS:
                    match = pattern_config['pattern'].search(line)
                    if match:
                        # Extract transaction data using pattern groups
                        date = match.group(pattern_config['groups']['date'])
                        amount_str = match.group(pattern_config['groups']['amount']).replace(',', '')
                        description = match.group(pattern_config['groups']['description']).strip()
                        
                        # The date from the pattern already includes the year
                        date_with_year = date
                        
                        # Check if this is a credit transaction
                        if "CR" in line:
                            amount = f"-{amount_str}"  # Negative for credits
                            description = description.replace("CR", "").strip()
                        else:
                            amount = amount_str
                        
                        transactions.append({
                            'Transaction Date': date_with_year,
                            'Transaction Details': description,
                            'Amount': amount
                        })
                        
                        if self.debug_mode:
                            self.logger.debug(f"Extracted: Date={date_with_year}, Amount={amount}, Description={description}")
                        
                        # Found a match, no need to try other patterns
                        break
            
            if self.debug_mode:
                self.logger.debug(f"Total raw transactions found: {len(transactions)}")
            
            return self.clean_transactions(transactions)
        except Exception as e:
            raise TransactionExtractionError(f"Error extracting transactions: {str(e)}")
    
    def clean_transactions(self, transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Clean and standardize extracted transactions.
        
        Args:
            transactions (List[Dict[str, str]]): Raw transactions to clean
            
        Returns:
            List[Dict[str, str]]: Cleaned transactions
        """
        cleaned_transactions = []
        
        # Get statement period from first page
        statement_period = None
        for line in self.statement_text.split('\n'):
            if '(from' in line and 'to' in line:
                match = re.search(r'from (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})', line)
                if match:
                    statement_period = {
                        'start': datetime.strptime(match.group(1), '%d/%m/%Y'),
                        'end': datetime.strptime(match.group(2), '%d/%m/%Y')
                    }
                    break
        
        # Determine default year for dates without year
        default_year = statement_period['start'].year if statement_period else self.current_year
        
        for trans in transactions:
            # Skip empty transactions or headers
            if not trans['Transaction Details'] or trans['Transaction Details'] == 'Transaction details':
                continue
            
            # Clean up transaction details
            trans['Transaction Details'] = ' '.join(trans['Transaction Details'].split())
            
            # Try to standardize the date format
            try:
                # First try parsing with year
                try:
                    date_obj = datetime.strptime(trans['Transaction Date'], '%d %b %Y')
                except ValueError:
                    # If that fails, add the default year and try parsing
                    date_str_with_year = f"{trans['Transaction Date']} {default_year}"
                    date_obj = datetime.strptime(date_str_with_year, '%d %b %Y')
                    
                    # If we have a statement period, check if we need to adjust the year
                    if statement_period:
                        # If the date is before the statement start and it's a valid date,
                        # it might be from the next year
                        if date_obj < statement_period['start']:
                            date_obj = date_obj.replace(year=statement_period['end'].year)
                
                trans['Transaction Date'] = date_obj.strftime(DATE_FORMATS['output'])
            except ValueError as e:
                # Keep original format if parsing fails
                self.logger.warning(f"Could not parse date: {trans['Transaction Date']} - {str(e)}")
            
            cleaned_transactions.append(trans)
        
        if self.debug_mode:
            self.logger.debug(f"Cleaned transactions: {len(cleaned_transactions)}")
        
        return cleaned_transactions
    
    def write_to_csv(self, transactions: List[Dict[str, str]], output_path: str) -> None:
        """
        Write transactions to a CSV file.
        
        Args:
            transactions (List[Dict[str, str]]): Transactions to write
            output_path (str): Path to output CSV file
            
        Raises:
            OutputError: If there's an error writing the CSV
        """
        try:
            with open(output_path, 'w', newline='', encoding=FILE_SETTINGS['encoding']) as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=CSV_SETTINGS['fieldnames'],
                    delimiter=CSV_SETTINGS['delimiter'],
                    quotechar=CSV_SETTINGS['quotechar'],
                    quoting=getattr(csv, CSV_SETTINGS['quoting'])
                )
                writer.writeheader()
                
                if not transactions:
                    self.logger.warning("No transactions to write.")
                    return
                
                for transaction in transactions:
                    writer.writerow(transaction)
            
            self.logger.info(f"Successfully wrote {len(transactions)} transactions to {output_path}")
        except Exception as e:
            raise OutputError(f"Error writing to CSV: {str(e)}")
    
    def process_statement(self, pdf_path: str, output_path: str = None) -> None:
        """
        Process a credit card statement PDF and extract transactions.
        
        Args:
            pdf_path (str): Path to the PDF file
            output_path (str, optional): Path for the output CSV file. If not provided,
                                       will use the input filename with .csv extension.
        """
        try:
            # Validate PDF
            self.validate_pdf(pdf_path)
            
            # Extract text from PDF
            self.statement_text = self.extract_text_from_pdf(pdf_path)
            
            # Extract transactions
            transactions = self.extract_transactions(self.statement_text)
            
            # Determine output path
            if output_path is None:
                # Use input filename but replace .pdf with .csv
                output_path = os.path.splitext(pdf_path)[0] + '.csv'
            
            # Write to CSV
            self.write_to_csv(transactions, output_path)
            
            # Print summary
            print(f"\nProcessed {len(transactions)} transactions")
            print(f"Output written to: {output_path}")
            
            if self.debug_mode:
                debug_path = os.path.splitext(pdf_path)[0] + '_debug.txt'
                with open(debug_path, 'w', encoding=FILE_SETTINGS['encoding']) as f:
                    f.write(self.statement_text)
                print(f"Debug output written to: {debug_path}")
                
        except Exception as e:
            self.logger.error(f"Error processing statement: {str(e)}")
            raise

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Extract transactions from credit card statement PDFs")
    parser.add_argument("pdf_path", nargs="?", help="Path to the PDF file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--output", "-o", help="Path to output CSV file (default: input_filename_transactions.csv)")
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Create extractor
    extractor = StatementExtractor(debug_mode=args.debug)
    
    # Get PDF path
    pdf_path = args.pdf_path
    if not pdf_path:
        pdf_path = input("Enter the path to your PDF file: ").strip()
    
    # Process the statement
    extractor.process_statement(pdf_path, output_path=args.output)

if __name__ == "__main__":
    main()