import pandas as pd
import logging
from typing import List, Dict
from utils import print_header

class ExcelExporter:
    """Handles exporting data to Excel files."""
    
    def __init__(self, output_excel_path: str):
        self.output_excel_path = output_excel_path
    
    def export_to_excel(self, data: List[Dict]) -> bool:
        """Export extracted data to Excel file."""
        if not data:
            logging.warning("No data to export to Excel")
            print("\n  No PDFs met the requirements. Excel file will not be created.")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file with formatting
        try:
            with pd.ExcelWriter(self.output_excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='PDF_Extracted_Data', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['PDF_Extracted_Data']
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Freeze the header row
                worksheet.freeze_panes = 'A2'
            
            print(f"\n Data successfully exported to: {self.output_excel_path}")
            logging.info(f"Data exported to {self.output_excel_path}")
            logging.info(f"Total PDFs processed and included: {len(data)}")
            
            # Show preview
            self._show_preview(df)
            return True
            
        except Exception as e:
            logging.error(f"Error exporting to Excel: {str(e)}")
            print(f"\n❌ Error creating Excel file: {str(e)}")
            return False
    
    def _show_preview(self, df: pd.DataFrame):
        """Show preview of the Excel data."""
        print_header(" EXCEL FILE PREVIEW (first 5 rows)")
        print(df.head().to_string())
        print("="*60)
    
    def print_summary(self, data: List[Dict], requirement_handler) -> None:
        """Print a summary of the processing."""
        print_header(" PROCESSING SUMMARY")
        
        if data:
            print(f" Total PDFs meeting requirements: {len(data)}")
            
            print("\n Files included:")
            for i, item in enumerate(data[:10], 1):
                print(f"  {i}. {item['filename']}")
            
            if len(data) > 10:
                print(f"  ... and {len(data) - 10} more")
            
            # Show statistics
            if requirement_handler and requirement_handler.requirement_patterns:
                print("\n Extraction Statistics:")
                for item in requirement_handler.requirement_patterns:
                    from utils import clean_key_name
                    key_name = f"has_{clean_key_name(item['name'])}"
                    found_count = sum(1 for d in data if d.get(key_name, False))
                    percentage = (found_count / len(data)) * 100 if data else 0
                    print(f"  • {item['name']}: found in {found_count}/{len(data)} PDFs ({percentage:.1f}%)")
        else:
            print(" No PDFs met the specified requirements.")
            print("\n Suggestions:")
            print("  1. Check if your requirements are too strict")
            print("  2. Verify the PDFs contain the information you're searching for")
            print("  3. Try using regex patterns that are more flexible")
        
        print("="*60)