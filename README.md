# CCS-Extract

A Python utility for extracting transaction data from credit card statement PDFs and converting them to CSV format.

[![Test Coverage](https://codecov.io/gh/BigAl/ccs-extract/branch/main/graph/badge.svg)](https://codecov.io/gh/BigAl/ccs-extract)
[![Tests](https://github.com/BigAl/ccs-extract/actions/workflows/coverage.yml/badge.svg)](https://github.com/BigAl/ccs-extract/actions/workflows/coverage.yml)
[![Docker Build](https://github.com/BigAl/ccs-extract/actions/workflows/docker.yml/badge.svg)](https://github.com/BigAl/ccs-extract/actions/workflows/docker.yml)


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
- Docker support for containerized execution

## Requirements

- Python 3.x
- pypdf
- tqdm
- jsonschema
- reportlab (for testing)

## Installation

### Option 1: Local Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ccs-extract.git
cd ccs-extract
```

2. Set up the virtual environment and install dependencies:
```bash
# Source the setup script (note the 'source' command)
source setup.sh
```

The setup script will:
- Create a Python virtual environment
- Activate the environment
- Install all required dependencies
- Create a configuration file from the template

The virtual environment will remain active in your current shell session. You can run the tool immediately after setup.

3. Copy the configuration template and customize it:
```bash
cp transaction_config.template.json transaction_config.json
```

4. Edit `transaction_config.json` to add your own merchant patterns and categories

### Option 2: Docker Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ccs-extract.git
cd ccs-extract
```

2. Create necessary directories:
```bash
mkdir -p input output
```

3. Copy and customize the configuration:
```bash
cp transaction_config.template.json transaction_config.json
```

4. Build and run with Docker:
```bash
# Build the Docker image
docker build -t ccs-extract .

# Run the container
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output -v $(pwd)/transaction_config.json:/app/transaction_config.json ccs-extract
```

The Docker setup will:
- Create a containerized environment
- Mount input/output directories
- Use your configuration file
- Process PDF files from the input directory
- Save results to the output directory

## Development

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ccs-extract.git
   cd ccs-extract
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   pytest
   ```

### Running Tests

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

### Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **MyPy**: Static type checking
- **pre-commit**: Git hooks for code quality

These tools are automatically run on every commit. To run them manually:

```bash
pre-commit run --all-files
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. The release workflow will automatically publish to PyPI

### Deactivating the Virtual Environment

When you're done using the tool, you can deactivate the virtual environment:
```bash
deactivate
```

### Using the Tool

With the virtual environment activated, you can run the tool as described in the Usage section below.

## Usage

### Command Line Usage

```bash
python ccs_extract.py [pdf_file_path] [--debug] [--output OUTPUT_FILE] [--validate-config]
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
- Validate configuration file:
  ```bash
  python ccs_extract.py --validate-config
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

### Configuration File

The script can use an optional JSON configuration file (`transaction_config.json`) to customize merchant patterns and transaction categories. If the file doesn't exist, the script will use comprehensive default patterns that cover common merchants and categories.

To customize the patterns:
1. The script will create a default configuration file if none exists
2. Edit the patterns in the file to match your needs
3. The configuration has two main sections:
   - `merchant_patterns`: Rules for normalizing merchant names
   - `categories`: Keywords for categorizing transactions

Example pattern:
```json
{
    "pattern": "(?i)woolworths(?:\\s+supermarket)?|woolies",
    "normalized": "Woolworths"
}
```

Example category:
```json
"Groceries": [
    "woolworths",
    "coles",
    "aldi",
    "supermarket"
]
```

If you prefer to use the default patterns (recommended), simply delete the configuration file and the script will use its built-in comprehensive patterns.

### Security Considerations

#### Docker Security
The Docker container runs with enhanced security:
- A non-root user (`appuser`)
- Secure file permissions:
  - Directories: 755 (owner: rwx, group: r-x, others: r-x)
  - Files: 644 (owner: rw-, group: r--, others: r--)
- Write access restricted to the output directory
- Read-only access to input and configuration files
- No unnecessary permissions granted

#### Configuration Security
The default patterns are built into the code, eliminating the need for a separate configuration file. If you choose to use a custom configuration file, it should be kept private as it may contain information about your spending patterns. The file is automatically added to `.gitignore` to prevent accidental commits.

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