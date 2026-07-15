import logging
from typing import Dict, Any

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def clean_key_name(name: str) -> str:
    """Convert a name to a clean key format."""
    return name.lower().replace(' ', '_').replace('-', '_')

def format_list_for_excel(items: list, max_items: int = 10) -> str:
    """Format a list for Excel export."""
    if not items:
        return ""
    return ', '.join(str(v) for v in items[:max_items])

def print_header(title: str, width: int = 60):
    """Print a formatted header."""
    print("\n" + "="*width)
    print(f" {title} ")
    print("="*width)

def print_subheader(title: str, width: int = 60):
    """Print a formatted subheader."""
    print("\n" + "-"*width)
    print(f" {title} ")
    print("-"*width)