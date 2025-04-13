"""
Logging configuration for CCS-Extract.
"""

import logging
from config import LOG_SETTINGS

def setup_logger(name: str) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(LOG_SETTINGS['level'])
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_SETTINGS['level'])
        
        # Create formatter
        formatter = logging.Formatter(
            LOG_SETTINGS['format'],
            datefmt=LOG_SETTINGS['date_format']
        )
        
        # Add formatter to handler
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger 