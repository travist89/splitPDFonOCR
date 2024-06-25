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

    extracted_text_for_naming = ""  # Initialize the variable for naming files

    for page_num in range(num_pages):
        page = document.load_page(page_num)

        # Convert PDF page to image
        images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
        image = images[0]

        # Extract text from image using OCR
        text = ocr_text_from_image(image)

        if search_text in text:
            start_index = text.index(search_text) + len(search_text)
            extracted_text = text[start_index : start_index + 8].strip()

            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                extracted_text = extracted_text.replace(char, '')

            if extracted_text_for_naming and page_num > split_start:
                pdf_writer = PdfWriter()
                for i in range(split_start, page_num):
                    pdf_writer.add_page(pdf_reader.pages[i])

                base_filename = f"{extracted_text_for_naming}.pdf"
                output_filename = os.path.join(output_dir, base_filename)
                file_exists = os.path.isfile(output_filename)
                copy_number = 1
                while file_exists:
                    base_filename = f"{extracted_text_for_naming} (copy {copy_number}).pdf"
                    output_filename = os.path.join(output_dir, base_filename)
                    file_exists = os.path.isfile(output_filename)
                    copy_number += 1

                with open(output_filename, 'wb') as output_pdf:
                    pdf_writer.write(output_pdf)
                print(f"Created: {output_filename}")
                split_number += 1
                split_start = page_num
                
            extracted_text_for_naming = extracted_text  # Update the naming text for the next file

    # Handle the last split
    if split_start < num_pages:
        pdf_writer = PdfWriter()
        for i in range(split_start, num_pages):
            pdf_writer.add_page(pdf_reader.pages[i])

        if extracted_text_for_naming:
            output_filename = os.path.join(output_dir, f"{extracted_text_for_naming}.pdf")
        else:
            output_filename = os.path.join(output_dir, f'split_{split_number}.pdf')

        with open(output_filename, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
        print(f"Created: {output_filename}")

# Example usage:
pdf_path = 'example.pdf'  # Replace with your PDF file path
search_text = 'Statement Date '  # Replace with the text you want to split by
output_dir = 'output'  # Directory to save the split files
split_pdf_by_ocr_text(pdf_path, search_text, output_dir)
