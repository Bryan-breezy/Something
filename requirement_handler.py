from typing import Dict, List, Any, Optional
from pattern_detector import PatternDetector
from utils import clean_key_name, print_header, print_subheader

class RequirementHandler:
    """Handles user requirement collection and checking."""
    
    def __init__(self):
        self.requirement_patterns = []
        self.required_items = []
    
    def get_user_requirements(self, sample_text: str = "") -> None:
        """Ask user for their search requirements."""
        print_header("📋 PDF SCRAPING REQUIREMENTS SETUP")
        print("\nThis tool will help you extract specific information from PDFs.")
        print("You can search for items like: dates, transaction codes, references, amounts, etc.\n")
        
        # Get search patterns from user
        while True:
            print_subheader(f"Item #{len(self.requirement_patterns) + 1}")
            item_name = input("What are you looking for? (e.g., 'Transaction Date', 'Reference Number')\nEnter name or 'done' to finish: ").strip()
            
            if item_name.lower() == 'done':
                if len(self.requirement_patterns) == 0:
                    print("\n⚠️  You haven't added any search items. Please add at least one item.")
                    continue
                break
            
            if not item_name:
                print("❌ Item name cannot be empty. Please try again.")
                continue
            
            self._handle_item_input(item_name, sample_text)
        
        # Ask about required conditions
        if self.requirement_patterns:
            self._get_required_items()
            self._print_summary()
    
    def _handle_item_input(self, item_name: str, sample_text: str):
        """Handle input for a single search item."""
        print(f"\nHow would you like to find '{item_name}'?")
        print("1. 🔍 Enter a regex pattern (recommended for codes/references)")
        print("2. 📝 Enter keywords to search for")
        print("3. 🤖 Auto-detect common pattern")
        print("4. 👁️  Preview PDF content to help decide")
        
        choice = input("\nChoose option (1/2/3/4): ").strip()
        
        if choice == '1':
            self._handle_regex_input(item_name, sample_text)
        elif choice == '2':
            self._handle_keyword_input(item_name)
        elif choice == '3':
            self._handle_auto_detect(item_name, sample_text)
        elif choice == '4':
            self._handle_preview(sample_text)
            # Recursively try again
            self._handle_item_input(item_name, sample_text)
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, or 4.")
            self._handle_item_input(item_name, sample_text)
    
    def _handle_regex_input(self, item_name: str, sample_text: str):
        """Handle regex pattern input."""
        print(PatternDetector.get_regex_tips())
        pattern = input("\nEnter regex pattern: ").strip()
        
        if pattern:
            # Test pattern on sample text if available
            if sample_text:
                test_matches = PatternDetector.test_pattern(pattern, sample_text)
                if test_matches:
                    print(f"✓ Pattern found {len(test_matches)} match(es) in sample: {test_matches[:3]}")
                else:
                    print("⚠️  Pattern didn't match anything in the sample PDF. You can still continue.")
            
            self.requirement_patterns.append({
                'name': item_name,
                'type': 'regex',
                'pattern': pattern
            })
            print(f"✓ Added '{item_name}' with regex pattern")
    
    def _handle_keyword_input(self, item_name: str):
        """Handle keyword input."""
        keywords = input("Enter keywords (comma-separated, e.g., 'total, amount, sum'): ").strip()
        if keywords:
            keyword_list = [k.strip().lower() for k in keywords.split(',')]
            self.requirement_patterns.append({
                'name': item_name,
                'type': 'keyword',
                'keywords': keyword_list
            })
            print(f"✓ Added '{item_name}' with keywords: {', '.join(keyword_list)}")
    
    def _handle_auto_detect(self, item_name: str, sample_text: str):
        """Handle auto-detection of patterns."""
        auto_item = PatternDetector.auto_detect(item_name, sample_text)
        if auto_item:
            self.requirement_patterns.append(auto_item)
            print(f"✓ Auto-detected pattern for '{item_name}' as {auto_item['display_name']}")
            if sample_text and auto_item['type'] == 'regex':
                test_matches = PatternDetector.test_pattern(auto_item['pattern'], sample_text)
                if test_matches:
                    print(f"  Found examples: {test_matches[:3]}")
        else:
            print("❌ Could not auto-detect. Please use regex or keyword option.")
    
    def _handle_preview(self, sample_text: str):
        """Handle PDF content preview."""
        if sample_text:
            print_header("PDF PREVIEW (first 1000 characters)")
            print(sample_text[:1000])
            print_header("End of Preview")
        else:
            print("❌ No sample text available to preview.")
    
    def _get_required_items(self):
        """Get which items are required."""
        print_header("✅ CONDITIONS FOR INCLUDING PDF")
        print("\nA PDF will be included ONLY if it contains specific items.")
        print("For each item, decide if it's REQUIRED or OPTIONAL.\n")
        
        for i, item in enumerate(self.requirement_patterns, 1):
            print(f"{i}. {item['name']}")
            include = input(f"   Must '{item['name']}' be present? (y/n): ").strip().lower()
            if include == 'y':
                self.required_items.append(item['name'])
                print(f"   ✓ '{item['name']}' is REQUIRED")
            else:
                print(f"   → '{item['name']}' is OPTIONAL (will still extract if found)")
    
    def _print_summary(self):
        """Print summary of requirements."""
        print_header("📊 SUMMARY OF REQUIREMENTS")
        print(f"Total search items: {len(self.requirement_patterns)}")
        print(f"Required items: {len(self.required_items)}")
        if self.required_items:
            print(f"  - Required: {', '.join(self.required_items)}")
        print("="*60)
    
    def check_requirements(self, text: str) -> Dict[str, Any]:
        """Check requirements against PDF text."""
        requirements_met = {}
        
        # Search for all items in the text
        for item in self.requirement_patterns:
            if item['type'] == 'regex':
                self._check_regex_item(text, item, requirements_met)
            elif item['type'] == 'keyword':
                self._check_keyword_item(text, item, requirements_met)
        
        # Check if all required items are present
        all_required_met = True
        for req_item in self.required_items:
            key_name = f"has_{clean_key_name(req_item)}"
            if not requirements_met.get(key_name, False):
                all_required_met = False
                break
        
        requirements_met["all_requirements_met"] = all_required_met
        return requirements_met
    
    def _check_regex_item(self, text: str, item: Dict, requirements_met: Dict):
        """Check a regex-based item."""
        matches = PatternDetector.test_pattern(item['pattern'], text)
        found = len(matches) > 0
        key_name = f"has_{clean_key_name(item['name'])}"
        requirements_met[key_name] = found
        requirements_met[f"{clean_key_name(item['name'])}_values"] = matches if matches else []
    
    def _check_keyword_item(self, text: str, item: Dict, requirements_met: Dict):
        """Check a keyword-based item."""
        found_keywords = [k for k in item['keywords'] if k in text.lower()]
        found = len(found_keywords) > 0
        key_name = f"has_{clean_key_name(item['name'])}"
        requirements_met[key_name] = found
        requirements_met[f"{clean_key_name(item['name'])}_keywords_found"] = found_keywords
    
    def should_include_pdf(self, requirements: Dict[str, Any]) -> bool:
        """Determine if PDF should be included based on user's requirements."""
        return requirements.get("all_requirements_met", False)
    
    def extract_found_data(self, requirements: Dict) -> Dict:
        """Extract specific data points that were found during requirement check."""
        extracted_info = {}
        
        for key, value in requirements.items():
            if key.endswith('_values') and value:
                item_name = key.replace('_values', '').replace('_', ' ').title()
                extracted_info[item_name] = value[:5] if len(value) > 5 else value
            elif key.endswith('_keywords_found') and value:
                item_name = key.replace('_keywords_found', '').replace('_', ' ').title()
                extracted_info[f"{item_name} (keywords)"] = value
        
        return extracted_info