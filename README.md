# CCS-Extract

A Python utility for extracting transaction data from credit card statement PDFs and converting them to CSV format.

## Features

- Extracts transaction data from credit card statement PDFs
- Converts extracted data to CSV format
- Supports multiple date formats (with and without year)
- Automatically determines transaction year from statement period
- Handles both debit and credit transactions
- Supports debug mode for troubleshooting
- Provides transaction summary statistics
- Compatible with Python 3.15+ (no deprecation warnings)
- Customizable output file location
- Normalizes merchant names
- Categorizes transactions automatically

## Requirements

- Python 3.x
- pypdf
- tqdm

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ccs-extract.git
cd ccs-extract
```

2. Install the required dependencies:
```bash
pip install pypdf tqdm
```

## Usage

### Command Line Usage

```bash
python ccs_extract.py [pdf_file_path] [--debug] [--output OUTPUT_FILE]
```

Examples:
- Process a specific PDF file:
  ```bash
  python ccs_extract.py statement.pdf
  ```
- Process with debug output:
  ```bash
  python ccs_extract.py statement.pdf --debug
  ```
- Specify custom output file:
  ```bash
  python ccs_extract.py statement.pdf --output my_transactions.csv
  ```
- Run in interactive mode:
  ```bash
  python ccs_extract.py
  ```

### Output

The script generates two types of output files:
1. `[input_filename].csv` (default) or custom output file: Contains the extracted transaction data
2. `[input_filename]_debug.txt`: Contains raw PDF text (only generated in debug mode)

The CSV file includes the following columns:
- Transaction Date (in DD/MM/YYYY format)
- Merchant (normalized merchant name)
- Category (transaction category)
- Transaction Details (original description)
- Amount (negative for credits)

### Transaction Categories

The script automatically categorizes transactions into the following categories:
- Groceries (supermarkets, food stores)
- Dining (restaurants, cafes, pubs)
- Transport (public transport, taxis, ride-sharing)
- Entertainment (streaming services, movies, theatre)
- Shopping (retail stores, online shopping)
- Utilities (energy, internet, phone)
- Health (pharmacies, medical services)
- Education (schools, universities, courses)
- Insurance (vehicle, home, health insurance)
- Other (uncategorized transactions)

### Merchant Normalization

Common merchant names are normalized to consistent formats. For example:
- "WOOLWORTHS" or "WOOLIES" → "Woolworths"
- "COLES SUPERMARKET" → "Coles"
- "NETFLIX.COM" → "Netflix"
- "UBER *TRIP" → "Uber"

### Date Handling

The script handles dates in the following formats:
- Dates with year: "15 Mar 2025"
- Dates without year: "15 Mar"

When a date doesn't include a year, the script:
1. Attempts to extract the statement period from the PDF
2. Uses the statement period to determine the correct year
3. Falls back to the current year if no statement period is found

The script is designed to be compatible with future Python versions (3.15+) by avoiding ambiguous date parsing that could trigger deprecation warnings.

### Transaction Types

The script automatically detects:
- Regular transactions (positive amounts)
- Credit transactions (marked with "CR", shown as negative amounts)
- Handles comma-separated amounts (e.g., "1,234.56")

## Debug Mode

When running with the `--debug` flag, the script will:
- Extract and save raw text from the PDF
- Print detailed information about the extraction process
- Show potential transaction lines being processed
- Display extraction statistics
- Save detailed debug information to a separate file

## Error Handling

The script includes comprehensive error handling for:
- File not found errors
- PDF parsing errors
- Data extraction issues
- Date parsing issues
- CSV writing errors

## Limitations

- The script assumes transactions follow specific patterns in the PDF:
  - Standard format with year: `15 Mar 2024 $123.45 GROCERY STORE`
  - Standard format without year: `15 Mar $123.45 GROCERY STORE`
  - Credit transactions are marked with "CR": `16 Mar $67.89 CR REFUND`
  - Amounts can include commas: `17 Mar $1,234.56 RESTAURANT`
- Date parsing requires either a full date or a statement period for accurate year assignment
- Transaction amounts must be in a standard format with dollar signs
- Credit transactions must be marked with "CR" in the statement

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.