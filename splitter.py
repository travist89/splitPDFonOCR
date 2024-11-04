import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import os

def ocr_text_from_image(image):
    """Extract text from an image using OCR."""
    return pytesseract.image_to_string(image, config='--psm 6')

def merge_copy_files(output_dir):
    """Merges files with "(copy)" in their names in the given directory."""
    pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
    for filename in pdf_files:
        if "(copy" in filename:
            base_name = filename.split(" (copy")[0] + ".pdf"
            base_path = os.path.join(output_dir, base_name)
            copy_path = os.path.join(output_dir, filename)

            merger = PdfMerger()
            merger.append(base_path)
            merger.append(copy_path)
            merger.write(base_path)
            merger.close()

            os.remove(copy_path)  # Remove the copy file
            print(f"Merged {filename} into {base_name}")

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
            # Find the last occurrence of search_text in the text
            last_occurrence_index = text.rfind(search_text) 
            start_index = last_occurrence_index + len(search_text)
            extracted_text = text[start_index : start_index + 3].strip()

            # start_index = text.index(search_text) + len(search_text)
            # extracted_text = text[start_index : start_index + 8].strip()

            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n']:
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
    merge_copy_files(output_dir)

# Example usage:
pdf_path = 'example.pdf'  # Replace with your PDF file path
search_text = 'Employee Number: '  # Replace with the text you want to split by
output_dir = 'output'  # Directory to save the split files
split_pdf_by_ocr_text(pdf_path, search_text, output_dir)