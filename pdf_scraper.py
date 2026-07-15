import logging
from pathlib import Path
from pdf_processor import PDFProcessor
from excel_exporter import ExcelExporter
from utils import setup_logging, print_header

class PDFScraper:
    """Main orchestrator for PDF scraping automation."""
    
    def __init__(self, pdf_folder_path: str, output_excel_path: str):
        """
        Initialize the PDF scraper.
        
        Args:
            pdf_folder_path: Path to folder containing PDF files
            output_excel_path: Path where Excel file will be saved
        """
        self.pdf_folder_path = Path(pdf_folder_path)
        self.output_excel_path = output_excel_path
        self.processor = None
        self.exporter = ExcelExporter(output_excel_path)
    
    def run(self) -> None:
        """Main execution method."""
        print_header(" PDF SCRAPING AUTOMATION TOOL")
        print(f" PDF Folder: {self.pdf_folder_path}")
        print(f" Output Excel: {self.output_excel_path}")
        print("="*60)
        
        # Check if folder exists
        if not self.pdf_folder_path.exists():
            logging.error(f"Folder {self.pdf_folder_path} does not exist")
            print(f"\n❌ Error: Folder '{self.pdf_folder_path}' not found!")
            print("Please check the path and try again.")
            return
        
        # Initialize processor
        self.processor = PDFProcessor(str(self.pdf_folder_path))
        
        # Process all PDFs
        extracted_data = self.processor.process_all_pdfs()
        
        # Export to Excel
        if extracted_data:
            self.exporter.export_to_excel(extracted_data)
            self.exporter.print_summary(extracted_data, self.processor.requirement_handler)
        else:
            print("\n  No data was extracted. Excel file was not created.")
        
        print("\n Automation complete!")