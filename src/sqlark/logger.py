"""
Logging configuration
"""

import logging


def get_logger(name):
    """
    Returns a preconfigured logger
    """
    return logging.getLogger(name)
