import re
from typing import Dict, List, Any, Optional

class PatternDetector:
    """Handles auto-detection of common patterns in text."""
    
    # Common patterns for different types of data
    PATTERNS = {
        'date': {
            'patterns': [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
                r'\b\d{4}-\d{1,2}-\d{1,2}\b',          # YYYY-MM-DD
                r'\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
                r'\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b',    # DD Month YYYY
            ],
            'display_name': 'Date'
        },
        'transaction': {
            'patterns': [
                r'\bTXN:\s*([A-Z0-9-]+)\b',
                r'\bTRANSACTION:\s*([A-Z0-9-]+)\b',
                r'\bTRX:\s*([A-Z0-9-]+)\b',
                r'\b(?=[A-Z0-9]*\d)[A-Z0-9]{8,}\b',
            ],
            'display_name': 'Transaction Code'
        },
        'reference': {
            'patterns': [
                # UE reference patterns (priority)
                r'\bUE\s*:\s*([A-Z0-9-]+)',           # UE:12345
                r'\bUE\s+([A-Z0-9-]+)',                # UE 12345
                r'\bUE([A-Z0-9-]+)',                   # UE12345
                r'\bUE[-.\s]?([A-Z0-9]{4,})',          # UE-12345, UE.12345, UE 12345
                r'\bUE\d{6,}\b',                       # UE123456 (6+ digits)
                r'\bUE[A-Z0-9]{4,}\b',                 # UE1A2B3C (4+ alphanumeric)
            ],
            'display_name': 'Reference Number (UE references prioritized)'
        },
        'invoice': {
            'patterns': [
                r'\bINV:\s*([A-Z0-9-]+)\b',
                r'\bINVOICE:\s*([A-Z0-9-]+)\b',
                r'\bINVOICE\s*#\s*([A-Z0-9-]+)\b',
                r'\bINV-\d{6,}\b',
            ],
            'display_name': 'Invoice Number'
        },
        'amount': {
            'patterns': [
                r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP)',
                r'(?:total|amount|sum)[:\s]*\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
            ],
            'display_name': 'Amount'
        },
        'code': {
            'patterns': [
                r'\b[A-Z]{2,5}[0-9]{4,}\b',
                r'\b[0-9]{6,}\b',
            ],
            'display_name': 'Code'
        },
        'phone': {
            'patterns': [
                r'(?:(?:\+?254|0)(?:7|1)\d{2}[-.\s]?\d{3}[-.\s]?\d{3})',
            ],
            'display_name': 'Phone Number (Kenyan: +254, 07, or 01)'
        },
        'email': {
            'patterns': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            'display_name': 'Email'
        }
    }
    
    @classmethod
    def auto_detect(cls, item_name: str, sample_text: str = "") -> Optional[Dict[str, Any]]:
        """Auto-detect common patterns based on item name."""
        item_name_lower = item_name.lower()
        
        # Find matching pattern category
        for key, pattern_info in cls.PATTERNS.items():
            if key in item_name_lower:
                return {
                    'name': item_name,
                    'display_name': pattern_info['display_name'],
                    'type': 'regex',
                    'pattern': '|'.join(pattern_info['patterns'])
                }
        
        return None
    
    @classmethod
    def test_pattern(cls, pattern: str, text: str) -> List[str]:
        """Test a regex pattern on sample text."""
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches and isinstance(matches[0], tuple):
                flattened = []
                for m in matches:
                    if not m:
                        continue
                    if isinstance(m, tuple):
                        selected = next((group for group in m if group), m[0])
                        flattened.append(selected)
                    else:
                        flattened.append(m)
                return flattened
            return matches
        except re.error:
            return []
    
    @classmethod
    def get_regex_tips(cls) -> str:
        """Return regex tips for users."""
        return """
 Regex tips:
  - \\d matches any digit
  - [A-Z] matches uppercase letters
  - \\w matches letters, digits, underscore
  - {n} matches exactly n times
  - Example for transaction code: [A-Z]{2}[0-9]{6}
  - Example for date: \\d{2}/\\d{2}/\\d{4}
        """