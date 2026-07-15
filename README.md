# PDF to Excel Scraper

A simple PDF scraping automation tool that extracts text from PDFs based on user-defined requirements and exports the results to Excel.

## Requirements

- Python 3.8+
- pandas
- openpyxl
- PyPDF2

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Usage

1. Enter the folder path containing PDF files.
2. Enter the output Excel file name or press Enter to use the default.
3. Define search items and whether each item is required.
4. The tool processes PDFs, exports matching results to Excel, and prints a summary.
