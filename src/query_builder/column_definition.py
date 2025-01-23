"""
Module for a column definition
"""
from dataclasses import dataclass

@dataclass
class ColumnDefinition:
    """
    Represents a column definition
    """
    table_name: str
    name: str
    data_type: str
    is_nullable: bool
    default: str
    is_list: bool = False
