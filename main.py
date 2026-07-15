#!/usr/bin/env python3
"""
PDF Scraping Automation Tool
Extracts data from PDFs based on user-defined requirements and exports to Excel.
"""

import sys
import logging
from pdf_scraper import PDFScraper
from utils import setup_logging, print_header

def main():
    """Main function to run the PDF scraper."""
    print_header("🚀 PDF to Excel Scraper")
    
    # Setup logging
    setup_logging()
    
    # Get folder path from user
    while True:
        pdf_folder = input("\n📁 Enter the path to the folder containing PDF files: ").strip()
        if pdf_folder:
            break
        print("❌ Please enter a valid folder path.")
    
    # Get output Excel path
    default_output = "extracted_pdf_data.xlsx"
    output_excel = input(f"\n📄 Enter output Excel file name (press Enter for '{default_output}'): ").strip()
    if not output_excel:
        output_excel = default_output
    
    # Create and run scraper
    try:
        scraper = PDFScraper(pdf_folder, output_excel)
        scraper.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()