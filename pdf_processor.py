import PyPDF2
from PyPDF2.errors import PdfReadError
from tqdm import tqdm
import concurrent.futures
import os
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
                    text += page.extract_text() or ""
            return text
        except PdfReadError as e:
            logging.error(f"Error reading PDF content from {pdf_path}: {str(e)}")
            return ""
        except Exception as e:
            logging.error(f"Error reading {pdf_path}: {str(e)}")
            return ""
    
    def get_sample_text(self) -> str:
        """Get sample text from the first PDF for preview."""
        pdf_files = list(self.pdf_folder_path.glob("*.pdf"))
        if pdf_files:
            return self.extract_text_from_pdf(pdf_files[0])
        return ""
    
    def process_all_pdfs(self) -> List[Dict]:
        """Process all PDFs in the specified folder."""
        pdf_files = list(self.pdf_folder_path.glob("*.pdf"))
        
        if not pdf_files:
            logging.warning(f"No PDF files found in {self.pdf_folder_path}")
            return []
        
        logging.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Get sample text and setup requirements
        sample_text = self.get_sample_text()
        self.requirement_handler.get_user_requirements(sample_text)
        
        if not self.requirement_handler.requirement_patterns:
            print("\n No search items defined. Exiting...")
            return []
        
        print_header(" STARTING PDF PROCESSING")
        
        MAX_WORKERS = os.cpu_count() or 1 # Use all available CPU cores
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_pdf = {executor.submit(self._process_single_pdf, pdf_file): pdf_file for pdf_file in pdf_files}
            for future in tqdm(concurrent.futures.as_completed(future_to_pdf), total=len(pdf_files), desc="Processing PDFs"):
                pdf_file = future_to_pdf[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as exc:
                    logging.error(f"PDF {pdf_file.name} generated an exception: {exc}")
                    print(f"\n❌ Error processing {pdf_file.name}: {exc}")
        
        self.extracted_data = results
        print_header(f" Processing complete: {len(self.extracted_data)}/{len(pdf_files)} PDFs meet requirements")
        return self.extracted_data

    def _process_single_pdf(self, pdf_file: Path) -> Optional[Dict]:
        """Process a single PDF file."""
        logging.info(f"Processing: {pdf_file.name}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_file)
        
        if not text:
            logging.warning(f"No text extracted from {pdf_file.name}")
            return None
        
        # Check requirements
        requirements = self.requirement_handler.check_requirements(text)
        
        # Determine if PDF should be included
        if self.requirement_handler.should_include_pdf(requirements):
            # Extract additional data
            extracted_data = self.requirement_handler.extract_found_data(requirements)
            
            # Compile all data for this PDF
            pdf_data = self._compile_pdf_data(pdf_file, requirements, extracted_data)
            print(f"   INCLUDED - {pdf_file.name} meets all requirements")
            logging.info(f"Included {pdf_file.name} - requirements met")
            return pdf_data
        else:
            print(f"   SKIPPED - {pdf_file.name} missing required items")
            logging.info(f"Skipped {pdf_file.name} - requirements not met")
            return None
    
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
