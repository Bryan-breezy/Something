import PyPDF2
import logging
from pathlib import Path
from typing import List, Dict, Any
from requirement_handler import RequirementHandler
from utils import format_list_for_excel, print_header

class PDFProcessor:
    """Handles PDF file processing and text extraction."""
    
    def __init__(self, pdf_folder_path: str):
        self.pdf_folder_path = Path(pdf_folder_path)
        self.requirement_handler = RequirementHandler()
        self.extracted_data = []
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            return text
        except Exception as e:
            logging.error(f"Error reading {pdf_path}: {str(e)}")
            return ""
    
    def get_sample_text(self) -> str:
        """Get sample text from the first PDF for preview."""
        pdf_files = list(self.pdf_folder_path.glob("*.pdf"))
        if pdf_files:
            return self.extract_text_from_pdf(pdf_files[0])
        return ""
    
    def process_all_pdfs(self, profile_path: str = None) -> List[Dict]:
        """Process all PDFs in the specified folder.

        Args:
            profile_path: Optional path to a saved JSON requirements profile.
                If provided, requirements are loaded from it instead of
                prompting the user interactively - enabling unattended runs.
        """
        pdf_files = list(self.pdf_folder_path.glob("*.pdf"))
        
        if not pdf_files:
            logging.warning(f"No PDF files found in {self.pdf_folder_path}")
            return []
        
        logging.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Get sample text and setup requirements
        sample_text = self.get_sample_text()

        if profile_path:
            loaded = self.requirement_handler.load_profile(profile_path)
            if not loaded:
                print("\n Could not load requirements profile. Exiting...")
                return []
        else:
            self.requirement_handler.get_user_requirements(sample_text)
        
        if not self.requirement_handler.requirement_patterns:
            print("\n No search items defined. Exiting...")
            return []
        
        print_header(" STARTING PDF PROCESSING")
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            logging.info(f"Processing: {pdf_file.name}")
            
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_file)
            
            if not text:
                logging.warning(f"No text extracted from {pdf_file.name}")
                continue
            
            # Check requirements
            requirements = self.requirement_handler.check_requirements(text)
            
            # Determine if PDF should be included
            if self.requirement_handler.should_include_pdf(requirements):
                # Extract additional data
                extracted_data = self.requirement_handler.extract_found_data(requirements)
                
                # Compile all data for this PDF
                pdf_data = self._compile_pdf_data(pdf_file, requirements, extracted_data)
                self.extracted_data.append(pdf_data)
                print(f"  ✓ INCLUDED - meets all requirements")
                logging.info(f"Included {pdf_file.name} - requirements met")
            else:
                print(f"  ✗ SKIPPED - missing required items")
                logging.info(f"Skipped {pdf_file.name} - requirements not met")
        
        print_header(f" Processing complete: {len(self.extracted_data)}/{len(pdf_files)} PDFs meet requirements")
        return self.extracted_data
    
    def _compile_pdf_data(self, pdf_file: Path, requirements: Dict, extracted_data: Dict) -> Dict:
        """Compile all data for a single PDF."""
        pdf_data = {
            "filename": pdf_file.name,
            "file_path": str(pdf_file),
            "included": "Yes",
        }
        
        # Add all extracted items
        for key, value in requirements.items():
            if not key.startswith('_') and not callable(value):
                if isinstance(value, (list, dict)):
                    pdf_data[key] = format_list_for_excel(value)
                else:
                    pdf_data[key] = value
        
        # Add extracted specific data
        for key, value in extracted_data.items():
            clean_key = key.lower().replace(' ', '_')
            if isinstance(value, list):
                pdf_data[f"extracted_{clean_key}"] = format_list_for_excel(value)
            else:
                pdf_data[f"extracted_{clean_key}"] = value
        
        return pdf_data
