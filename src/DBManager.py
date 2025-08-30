"""
Legacy database manager - DEPRECATED

This file is kept for backward compatibility.
New code should use the database.py module instead.
"""

import warnings
from database import DatabaseManager

warnings.warn(
    "DBManager.py is deprecated. Use database.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Alias for backward compatibility
DBM = DatabaseManager