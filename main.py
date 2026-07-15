#!/usr/bin/env python3
"""
PDF Scraping Automation Tool
Extracts data from PDFs based on user-defined requirements and exports to Excel.

Usage:
    Interactive (first-time setup, prompts for folder/output/requirements):
        python main.py

    Unattended / scheduled (uses a previously saved requirements profile):
        python main.py --folder ./pdfs --output result.xlsx --profile profile.json

    A profile is created automatically the first time you run interactively
    and choose to save your requirements at the end of setup.
"""

import sys
import argparse
import logging
from pdf_scraper import PDFScraper
from utils import setup_logging, print_header


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract data from PDFs based on user-defined requirements and export to Excel."
    )
    parser.add_argument(
        "--folder", "-f",
        help="Path to the folder containing PDF files. If omitted, you'll be prompted."
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output Excel file path (default: extracted_pdf_data.xlsx)."
    )
    parser.add_argument(
        "--profile", "-p",
        default=None,
        help="Path to a saved JSON requirements profile. Skips interactive "
             "requirement setup entirely, enabling unattended/scheduled runs."
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR fallback for scanned/image-based PDFs (faster, but "
             "such PDFs will be skipped since no text can be extracted)."
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help="Max parallel worker processes for PDF text extraction "
             "(default: number of CPU cores)."
    )
    return parser.parse_args()


def main():
    """Main function to run the PDF scraper."""
    args = parse_args()
    print_header(" PDF to Excel Scraper")

    # Setup logging
    setup_logging()

    # Get folder path from args, or prompt if not provided
    pdf_folder = args.folder
    if not pdf_folder:
        while True:
            pdf_folder = input("\n Enter the path to the folder containing PDF files: ").strip()
            if pdf_folder:
                break
            print(" Please enter a valid folder path.")

    # Get output Excel path from args, or prompt if not provided
    default_output = "extracted_pdf_data.xlsx"
    output_excel = args.output
    if output_excel is None:
        if args.profile:
            # Unattended mode with no --output specified: just use the default
            output_excel = default_output
        else:
            output_excel = input(
                f"\n Enter output Excel file name (press Enter for '{default_output}'): "
            ).strip()
            if not output_excel:
                output_excel = default_output

    # Create and run scraper
    try:
        scraper = PDFScraper(
            pdf_folder, output_excel, profile_path=args.profile,
            enable_ocr=not args.no_ocr, max_workers=args.workers
        )
        scraper.run()
    except KeyboardInterrupt:
        print("\n\n  Process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n An unexpected error occurred: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
