"""
Custom exceptions for CCS-Extract.
"""

class StatementExtractorError(Exception):
    """Base exception for the statement extractor."""
    pass

class PDFError(StatementExtractorError):
    """Raised when there are issues with PDF file handling."""
    pass

class TransactionExtractionError(StatementExtractorError):
    """Raised when there are issues extracting transactions."""
    pass

class ValidationError(StatementExtractorError):
    """Raised when there are validation issues."""
    pass

class ConfigurationError(StatementExtractorError):
    """Raised when there are configuration issues."""
    pass

class OutputError(StatementExtractorError):
    """Raised when there are issues writing output."""
    pass 