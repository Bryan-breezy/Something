import sys
import logging
from pdf_scraper import PDFScraper
from utils import setup_logging, print_header

def main():
    """Main function to run the PDF scraper."""
    print_header(" PDF to Excel Scraper")
    
    # Setup logging
    setup_logging()
    
    # Get folder path from user
    while True:
        pdf_folder = input("\n Enter the path to the folder containing PDF files: ").strip()
        if not pdf_folder:
            print(" Folder path cannot be empty. Please try again.")
            continue
        from pathlib import Path
        if not Path(pdf_folder).is_dir():
            print(f" Error: Folder '{pdf_folder}' not found or is not a directory. Please enter a valid path.")
            continue
        import os
        if not os.access(pdf_folder, os.R_OK):
            print(f" Error: No read permissions for folder '{pdf_folder}'. Please check permissions.")
            continue
        break
    
    # Get output Excel path
    default_output = "extracted_pdf_data.xlsx"
    output_excel = input(f"\n Enter output Excel file name (press Enter for '{default_output}'): ").strip()
    if not output_excel:
        output_excel = default_output
    
    # Create and run scraper
    try:
        scraper = PDFScraper(pdf_folder, output_excel)
        scraper.run()
    except KeyboardInterrupt:
        print("\n\n  Process interrupted by user.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n Error: The specified folder or file was not found: {e}")
        logging.error(f"File not found error: {e}", exc_info=True)
        sys.exit(1)
    except PermissionError as e:
        print(f"\n Error: Permission denied to access the folder or file: {e}")
        logging.error(f"Permission error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n An unexpected error occurred: {e}")
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
