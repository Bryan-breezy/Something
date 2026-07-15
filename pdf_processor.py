import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple

import pdfplumber

from requirement_handler import RequirementHandler
from utils import format_list_for_excel, print_header

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - tqdm is a soft dependency
    tqdm = None

# Below this many characters per page on average, a PDF is treated as likely
# scanned/image-based rather than text-based, and OCR is attempted instead.
MIN_CHARS_PER_PAGE = 20


def _extract_with_pdfplumber(pdf_path: str) -> Tuple[str, int]:
    """Extract text using pdfplumber. Returns (text, page_count)."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts), page_count


def _extract_with_ocr(pdf_path: str) -> str:
    """Fall back to OCR for scanned/image-based PDFs.

    Requires the `pytesseract` and `pdf2image` Python packages AND the
    system binaries `tesseract-ocr` and `poppler-utils` to be installed.
    """
    import pytesseract
    from pdf2image import convert_from_path

    images = convert_from_path(pdf_path)
    text_parts = [pytesseract.image_to_string(img) for img in images]
    return "\n".join(text_parts)


def _extract_single_pdf(pdf_path: str, enable_ocr: bool) -> Dict[str, Any]:
    """Worker function: extract text from one PDF. Module-level so it can be
    pickled and run in a separate process via ProcessPoolExecutor."""
    result = {
        "path": pdf_path,
        "text": "",
        "method": "text",
        "error": None,
    }
    try:
        text, page_count = _extract_with_pdfplumber(pdf_path)
        avg_chars = len(text) / page_count if page_count else 0

        if avg_chars < MIN_CHARS_PER_PAGE:
            if enable_ocr:
                try:
                    ocr_text = _extract_with_ocr(pdf_path)
                    if len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        result["method"] = "ocr"
                except Exception as ocr_err:
                    result["error"] = f"OCR fallback failed: {str(ocr_err)}"
            else:
                result["method"] = "likely_scanned_no_ocr"

        result["text"] = text
    except Exception as e:
        result["error"] = str(e)

    return result


class PDFProcessor:
    """Handles PDF file processing and text extraction."""

    def __init__(self, pdf_folder_path: str, enable_ocr: bool = True, max_workers: int = None):
        self.pdf_folder_path = Path(pdf_folder_path)
        self.requirement_handler = RequirementHandler()
        self.extracted_data = []
        self.enable_ocr = enable_ocr
        self.max_workers = max_workers

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a single PDF file (sequential helper,
        used for sample-text preview and unit tests)."""
        result = _extract_single_pdf(str(pdf_path), self.enable_ocr)
        if result["error"] and not result["text"]:
            logging.error(f"Error reading {pdf_path}: {result['error']}")
        return result["text"]

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

        # Extract text from all PDFs in parallel - text extraction (and any
        # OCR fallback) is the expensive part, and each PDF is independent.
        extraction_results = {}
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(_extract_single_pdf, str(pdf_file), self.enable_ocr): pdf_file
                for pdf_file in pdf_files
            }
            iterator = as_completed(future_to_path)
            if tqdm:
                iterator = tqdm(iterator, total=len(pdf_files), desc="Extracting text")
            for future in iterator:
                pdf_file = future_to_path[future]
                try:
                    extraction_results[pdf_file] = future.result()
                except Exception as e:
                    extraction_results[pdf_file] = {
                        "path": str(pdf_file), "text": "", "method": "error", "error": str(e)
                    }

        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            logging.info(f"Processing: {pdf_file.name}")

            extraction = extraction_results[pdf_file]
            text = extraction["text"]

            if extraction.get("error"):
                logging.error(f"Error reading {pdf_file.name}: {extraction['error']}")

            if extraction.get("method") == "likely_scanned_no_ocr":
                print(f"    Likely a scanned/image-based PDF (little to no extractable text). "
                      f"OCR is disabled, so this file will be skipped.")
                logging.warning(f"{pdf_file.name} appears scanned; OCR disabled, no text extracted")
            elif extraction.get("method") == "ocr":
                print(f"    Little text found directly - used OCR fallback instead.")
                logging.info(f"{pdf_file.name} processed via OCR fallback")

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
                print(f"   INCLUDED - meets all requirements")
                logging.info(f"Included {pdf_file.name} - requirements met")
            else:
                print(f"  SKIPPED - missing required items")
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
