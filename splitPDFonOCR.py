import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
import os

def ocr_text_from_image(image):
    """Extract text from an image using OCR."""
    return pytesseract.image_to_string(image)


def split_pdf_by_ocr_text(pdf_path, search_text, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the original PDF
    document = fitz.open(pdf_path)
    num_pages = document.page_count
    split_start = 0
    split_number = 1

    # Create a PdfReader object
    pdf_reader = PdfReader(pdf_path)

    for page_num in range(num_pages):
        page = document.load_page(page_num)

        # Convert PDF page to image
        images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
        image = images[0]

        # Extract text from image using OCR
        text = ocr_text_from_image(image)

        if search_text in text:
            if page_num > split_start:
                # Create a new PDF writer object
                pdf_writer = PdfWriter()
                for i in range(split_start, page_num):
                    pdf_writer.add_page(pdf_reader.pages[i])
                
                # Save the split PDF
                output_filename = os.path.join(output_dir, f'split_{split_number}.pdf')
                with open(output_filename, 'wb') as output_pdf:
                    pdf_writer.write(output_pdf)
                
                print(f"Created: {output_filename}")
                split_number += 1
                split_start = page_num

    # Save the remaining pages after the last split
    if split_start < num_pages:
        pdf_writer = PdfWriter()
        for i in range(split_start, num_pages):
            pdf_writer.add_page(pdf_reader.pages[i])
        
        output_filename = os.path.join(output_dir, f'split_{split_number}.pdf')
        with open(output_filename, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
        
        print(f"Created: {output_filename}")


# Example usage:
pdf_path = 'example.pdf'  # Replace with your PDF file path
search_text = 'Endeavor'  # Replace with the text you want to split by
output_dir = 'output'  # Directory to save the split files
split_pdf_by_ocr_text(pdf_path, search_text, output_dir)
