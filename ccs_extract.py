#!/usr/bin/env python3
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
import json

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
    # Attempt to import core functional modules. If these fail, the script cannot run.
    from logger import setup_logger
    from exceptions import (
        StatementExtractorError,
        PDFError,
        TransactionExtractionError,
        ValidationError,
        OutputError
    )
    from transaction_rules import TransactionRulesEngine
except ImportError as e:
    # If core modules like config, logger, or exceptions are missing,
    # it's a fundamental issue. Log a critical error and exit.
    # A simple print is used here as logger might not be available.
    print(f"Critical Error: Failed to import core modules: {e}. "
          "Please ensure all modules (config.py, logger.py, exceptions.py) are correctly installed.", file=sys.stderr)
    sys.exit(1)

# Set up logger
# This line is now guaranteed to work, or the script would have exited.
logger = setup_logger(__name__)

class CreditCardStatementExtractor:
    """Main class for extracting transactions from credit card statements."""
    
    def __init__(self, config_file: str = "transaction_config.json"):
        """Initialize the extractor with configuration.
        
        Args:
            config_file: Path to the transaction configuration file
        """
        self.config = self._load_config(config_file)
        self.rules_engine = TransactionRulesEngine("transaction_rules.json")
        # Load transaction parsing patterns
        self.transaction_patterns = self._load_parsing_patterns("parsing_patterns.json")
        self.debug_mode = False
        self.logger = logger
        self.current_year = datetime.now().year
        self.statement_text = ""
        self.base_dir = os.getcwd()

    def _load_parsing_patterns(self, patterns_file: str) -> List[Dict[str, Any]]:
        """Load transaction parsing patterns from JSON file or use defaults."""
        try:
            with open(patterns_file, 'r') as f:
                custom_patterns_data = json.load(f)

            # Validate basic structure and compile regex
            loaded_patterns = []
            if not isinstance(custom_patterns_data, list):
                raise ValueError("Parsing patterns JSON must be a list.")

            for p_data in custom_patterns_data:
                if not isinstance(p_data, dict) or \
                   'name' not in p_data or \
                   'pattern' not in p_data or \
                   'groups' not in p_data:
                    raise ValueError("Invalid pattern structure in JSON.")

                # Compile the regex pattern
                p_data['pattern'] = re.compile(p_data['pattern'])
                loaded_patterns.append(p_data)

            self.logger.info(f"Successfully loaded {len(loaded_patterns)} custom parsing patterns from '{patterns_file}'.")
            return loaded_patterns
        except FileNotFoundError:
            self.logger.warning(f"Custom parsing patterns file '{patterns_file}' not found. Using default patterns from config.py.")
            # TRANSACTION_PATTERNS is imported from config.py
            return TRANSACTION_PATTERNS
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error loading or validating custom parsing patterns from '{patterns_file}': {e}. Using default patterns.")
            return TRANSACTION_PATTERNS
        except Exception as e:
            self.logger.error(f"Unexpected error loading custom parsing patterns from '{patterns_file}': {e}. Using default patterns.")
            return TRANSACTION_PATTERNS

    def _load_config(self, config_file: str) -> dict:
        """Load transaction categorization configuration from a file.
        
        Args:
            config_file: Path to the transaction configuration file
            
        Returns:
            dict: Loaded configuration
            
        Raises:
            StatementExtractorError: If there's an error loading the configuration
        """
        try:
            from transaction_categories import load_custom_config
            merchant_patterns, categories = load_custom_config(config_file)
            return {
                "merchant_patterns": merchant_patterns,
                "categories": categories
            }
        # FileNotFoundError is now handled within load_custom_config
        except (json.JSONDecodeError, ValidationError) as e:
            raise StatementExtractorError(f"Error loading transaction configuration from '{config_file}': {str(e)}")
    
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
                for pattern_config in self.transaction_patterns: # Use instance variable
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
            
            # Normalize merchant name and categorize transaction
            try:
                from transaction_categories import normalize_merchant, categorize_transaction
                trans['Merchant'] = normalize_merchant(trans['Transaction Details'])
                trans['Category'] = categorize_transaction(trans['Transaction Details'])
            except ImportError:
                # Fallback if transaction_categories module is not available
                trans['Merchant'] = trans['Transaction Details']
                trans['Category'] = 'Other'
            
            # Try to standardize the date format
            try:
                # First try parsing with year
                try:
                    date_obj = datetime.strptime(trans['Transaction Date'], '%d %b %Y')
                except ValueError:
                    # If that fails, add the default year and try parsing
                    date_str = f"{trans['Transaction Date']} {default_year}"
                    date_obj = datetime.strptime(date_str, '%d %b %Y')
                
                # Format date consistently
                trans['Transaction Date'] = date_obj.strftime(DATE_FORMATS['output'])
            except ValueError:
                self.logger.warning(f"Could not parse date: {trans['Transaction Date']}")
            
            cleaned_transactions.append(trans)
        
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
                                       will use the input filename with .csv extension in the output directory.
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
                # Use input filename but place in output directory with .csv extension
                input_filename = os.path.basename(pdf_path)
                base_filename = os.path.splitext(input_filename)[0] + '.csv'
                output_path = os.path.join(self.base_dir, 'output', base_filename)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
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

    def _categorize_transaction(self, description: str, amount: float, date: datetime) -> str:
        """Categorize a transaction using the rules engine.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            date: Transaction date
            
        Returns:
            Category name
        """
        # Try custom rules first
        category = self.rules_engine.apply_rules(description, amount, date)
        if category:
            return category
            
        # Fall back to default categories
        for category, patterns in self.config["categories"].items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return category
        return "Other"

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract transactions from credit card statements')
    parser.add_argument('pdf_file', nargs='?', help='PDF file to process')
    parser.add_argument('--output', help='Output CSV file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', help='Path to configuration file')

    args = parser.parse_args()

    # If no PDF file is provided, enter interactive mode
    if args.pdf_file is None:
        args.pdf_file = input('Enter the path to the PDF file: ')

    return args

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    try:
        extractor = CreditCardStatementExtractor(config_file=args.config)
        extractor.debug_mode = args.debug
        extractor.process_statement(args.pdf_file, args.output)
    except StatementExtractorError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()