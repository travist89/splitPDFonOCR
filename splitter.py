import os
import sys
import subprocess

# --- HIDE SUBPROCESS CONSOLE WINDOWS ON WINDOWS ---
# When running in a GUI or without a console, libraries that use subprocess
# (like pdf2image and pytesseract) will briefly flash a cmd window. 
# We patch subprocess.Popen to prevent this.
if os.name == 'nt':
    _original_popen = subprocess.Popen

    def _patched_popen(*args, **kwargs):
        if 'creationflags' not in kwargs:
            # CREATE_NO_WINDOW = 0x08000000
            kwargs['creationflags'] = 0x08000000
        return _original_popen(*args, **kwargs)

    subprocess.Popen = _patched_popen

import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- SETUP FOR PORTABILITY ---
def setup_dependencies():
    """Dynamically configure paths for Poppler and Tesseract dependencies.

    This function is crucial for making the application portable. It allows the script
    to find its dependencies (Poppler and Tesseract) whether it's being run as a
    normal Python script or as a frozen executable created by PyInstaller.
    """
    # A list of paths to search for the dependency folders.
    search_paths = []
    
    # The 'frozen' attribute is set to True by PyInstaller when the script is bundled.
    if getattr(sys, 'frozen', False):
        # When a one-file executable is run, PyInstaller extracts all bundled files
        # into a temporary directory. The path to this directory is stored in `sys._MEIPASS`.
        # We check this path first, as it's where bundled dependencies will be.
        if hasattr(sys, '_MEIPASS'):
            search_paths.append(sys._MEIPASS)
        # This allows for the "side-by-side" portable method, where the Poppler/Tesseract
        # folders are placed next to the executable.
        search_paths.append(os.path.dirname(sys.executable))
    else:
        # If not frozen, we're running as a standard .py script.
        # The dependencies are expected to be in the same directory as the script.
        search_paths.append(os.path.dirname(os.path.abspath(__file__)))

    # --- Configure Poppler ---
    # We need to add Poppler's 'bin' directory to the system's PATH environment variable
    # so that the `pdf2image` library can find its command-line tools.
    # The expected folder structure is `Poppler/Library/bin`.
    for base in search_paths:
        poppler_path = os.path.join(base, 'Poppler', 'Library', 'bin')
        if os.path.exists(poppler_path):
            os.environ["PATH"] += os.pathsep + poppler_path
            break # Stop searching once found.
    
    # --- Configure Tesseract ---
    # The `pytesseract` library needs to be told the exact location of the tesseract.exe file.
    # The expected folder structure is `Tesseract-OCR/tesseract.exe`.
    for base in search_paths:
        tesseract_exe = os.path.join(base, 'Tesseract-OCR', 'tesseract.exe')
        if os.path.exists(tesseract_exe):
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe
            break # Stop searching once found.

# Run the setup function as soon as the script is loaded.
setup_dependencies()

def ocr_text_from_image(image):
    """Extract text from a single image using Tesseract OCR.
    
    Args:
        image: A PIL Image object.
    Returns:
        A string containing the extracted text.
    """
    # '--psm 6' tells Tesseract to assume a single uniform block of text, which can improve accuracy.
    return pytesseract.image_to_string(image, config='--psm 6')

def merge_copy_files(output_dir):
    """Merges files with "(copy)" in their names in the given directory."""
    pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
    for filename in pdf_files:
        if "(copy" in filename:
            # Example: filename is "123 (copy 1).pdf", base_name becomes "123.pdf"
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

def generate_audit_report(output_dir):
    """Generates an HTML report with thumbnails of the split PDFs for easy verification."""
    print("\nGenerating HTML Audit Report...")
    
    audit_dir = os.path.join(output_dir, "Audit_Report")
    os.makedirs(audit_dir, exist_ok=True)
    
    html_content = """
    <html>
    <head>
        <title>PDF Split Audit Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ddd; padding: 15px; text-align: left; vertical-align: middle; }
            th { background-color: #0056b3; color: white; }
            img { max-width: 120px; border: 1px solid #ccc; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
            .review-needed { background-color: #fff3cd; }
            .note { color: #856404; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>PDF Split Audit Report</h1>
        <p>Please review the generated files below. Click on a file name or thumbnail to open the PDF.</p>
        <table>
            <tr>
                <th>Thumbnail (Page 1)</th>
                <th>Extracted ID</th>
                <th>File Name</th>
                <th>Total Pages</th>
                <th>Notes / Warnings</th>
            </tr>
    """
    
    pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
    
    for filename in pdf_files:
        pdf_path = os.path.join(output_dir, filename)
        emp_number = filename.replace('.pdf', '')
        
        # Open PDF to get page count and generate thumbnail
        doc = fitz.open(pdf_path)
        num_pages = doc.page_count
        
        thumb_filename = f"thumb_{emp_number}.png"
        thumb_path = os.path.join(audit_dir, thumb_filename)
        
        # Render the first page at 20% scale
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
        pix.save(thumb_path)
        doc.close()
        
        # Flag suspicious entries requiring human review
        notes = ""
        row_class = ""
        if len(emp_number) != 3 or not emp_number.isdigit():
            notes += "⚠️ Check ID format. "
            row_class = 'class="review-needed"'
        if num_pages > 20:  # Flag if an employee record seems suspiciously long
            notes += "⚠️ Unusually high page count. "
            row_class = 'class="review-needed"'
            
        html_content += f"""
            <tr {row_class}>
                <td><a href="../{filename}" target="_blank"><img src="{thumb_filename}" alt="Thumbnail"></a></td>
                <td><strong>{emp_number}</strong></td>
                <td><a href="../{filename}" target="_blank">{filename}</a></td>
                <td>{num_pages}</td>
                <td class="note">{notes}</td>
            </tr>
        """
        
    html_content += """
        </table>
    </body>
    </html>
    """
    
    report_path = os.path.join(audit_dir, "_Audit_Report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Audit report successfully created: {report_path}")

def split_pdf_by_ocr_text(pdf_path, search_text, output_dir, progress_callback=None):
    """Splits a PDF into multiple files based on OCR text found on each page.

    This is the core logic of the application. It iterates through a PDF, performs
    OCR on each page to find a specific text string (e.g., "Employee Number:"),
    and then splits the PDF into chunks, naming each chunk based on the text that
    was found.

    Args:
        pdf_path (str): The file path of the source PDF.
        search_text (str): The text to search for on each page to trigger a split.
        output_dir (str): The directory where the split PDF files will be saved.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open the original PDF
    document = fitz.open(pdf_path)
    num_pages = document.page_count
    split_start = 0

    # Create a PdfReader object
    pdf_reader = PdfReader(pdf_path)

    # This variable holds the employee number that will be used to name the *next* file.
    # When we find a keyword on page N, it signals the *end* of the previous employee's
    # section and the *start* of a new one. The file for the previous section is then
    # saved using the name we found earlier.
    extracted_text_for_naming = ""

    for page_num in range(num_pages):
        # Update the progress bar for the current page
        if progress_callback:
            progress_callback(page_num + 1, num_pages)

        page = document.load_page(page_num)

        # Convert the current PDF page to an image object for OCR.
        # This is done one page at a time to conserve memory.
        images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
        image = images[0]

        # Extract text from image using OCR
        text = ocr_text_from_image(image)

        # Check if our keyword (e.g., "Employee Number:") exists on the page.
        if search_text in text:
            # Find the last occurrence of the search text on the page.
            last_occurrence_index = text.rfind(search_text) 
            start_index = last_occurrence_index + len(search_text)
            
            # Extract the employee number. This logic is designed to be robust:
            # 1. `text[start_index:]`: Get all text *after* the search term.
            # 2. `.strip()`: Remove any leading/trailing whitespace. OCR can add unexpected spaces.
            # 3. `[:3]`: Take the first 3 characters of the result.
            extracted_text = text[start_index:].strip()[:3]

            # Sanitize the extracted text to ensure it's a valid filename.
            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n']:
                extracted_text = extracted_text.replace(char, '')

            # If `extracted_text_for_naming` has a value, it means we have a completed
            # section that needs to be saved.
            if extracted_text_for_naming and page_num > split_start:
                pdf_writer = PdfWriter()
                # Add all pages from the start of the current split up to (but not including)
                # the current page to the writer object.
                for i in range(split_start, page_num):
                    pdf_writer.add_page(pdf_reader.pages[i])

                # --- Handle file naming and potential duplicates ---
                # If a file with the same employee number already exists, append "(copy X)"
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

                # Set the start of the *next* split to the current page number.
                split_start = page_num
                
            # Update the naming text with the number we just found. This name will be
            # used for the file when the *next* split occurs, or at the end of the document.
            extracted_text_for_naming = extracted_text

    # --- Save the final section of the PDF ---
    # After the loop finishes, the last section (from the last found keyword to the
    # end of the document) needs to be saved.
    if split_start < num_pages:
        pdf_writer = PdfWriter()
        for i in range(split_start, num_pages):
            pdf_writer.add_page(pdf_reader.pages[i])

        # Use the last employee number found for the filename.
        if extracted_text_for_naming:
            output_filename = os.path.join(output_dir, f"{extracted_text_for_naming}.pdf")
        else:
            # Fallback name if no search text was ever found in the entire document.
            output_filename = os.path.join(output_dir, f'split_1.pdf')

        with open(output_filename, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
        print(f"Created: {output_filename}")
    # After all splits are done, merge any files that were created with "(copy)" in their name.
    merge_copy_files(output_dir)
    
    if progress_callback:
        progress_callback(-1, -1)
        
    # Finally, generate the HTML Audit report so users can easily verify the splits.
    generate_audit_report(output_dir)

def run_gui():
    """Launches the Tkinter Graphical User Interface."""
    root = tk.Tk()
    root.title("OCR PDF Splitter")
    root.geometry("550x290")
    root.resizable(False, False)

    # --- Set Application Logo ---
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    logo_path = os.path.join(base_path, 'top.ico')
    if os.path.exists(logo_path):
        try:
            root.iconbitmap(logo_path)
        except Exception as e:
            print(f"Could not load logo: {e}")

    # Variables to hold user input
    pdf_path_var = tk.StringVar()
    search_text_var = tk.StringVar(value='Employee Number:')
    output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), 'output'))

    def browse_pdf():
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            pdf_path_var.set(filepath)

    def choose_folder():
        folderpath = filedialog.askdirectory()
        if folderpath:
            output_dir_var.set(folderpath)

    def start_processing():
        pdf_path = pdf_path_var.get()
        search_text = search_text_var.get()
        output_dir = output_dir_var.get()

        # Input validation
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return
        if not search_text:
            messagebox.showerror("Error", "Please enter the search text.")
            return
        if not output_dir:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        # Update UI state
        btn_process.config(state=tk.DISABLED)
        lbl_status.config(text="Status: Processing... Please wait (OCR can take a while).")
        progress_var.set(0)

        def update_progress(current, total):
            if current == -1:
                lbl_status.config(text="Status: Generating Audit Report...")
                progress_var.set(100)
            else:
                progress_var.set((current / total) * 100)
                lbl_status.config(text=f"Status: Processing page {current} of {total}...")

        def run():
            try:
                split_pdf_by_ocr_text(pdf_path, search_text, output_dir, lambda c, t: root.after(0, update_progress, c, t))
                # Use root.after to safely update the GUI from the background thread
                root.after(0, lambda: messagebox.showinfo("Success", "Processing complete!\nPlease check the Audit_Report folder in your output directory."))
                root.after(0, lambda: lbl_status.config(text="Status: Idle"))
            except Exception as e:
                root.after(0, lambda err=e: messagebox.showerror("Error", f"An error occurred:\n{err}"))
                root.after(0, lambda: lbl_status.config(text="Status: Error"))
            finally:
                root.after(0, lambda: btn_process.config(state=tk.NORMAL))

        # Run the heavy OCR process in a background thread so the GUI doesn't freeze
        threading.Thread(target=run, daemon=True).start()

    # --- UI Layout ---
    padding = {'padx': 10, 'pady': 10}

    # Row 0: PDF File
    tk.Label(root, text="PDF File:").grid(row=0, column=0, sticky="e", **padding)
    tk.Entry(root, textvariable=pdf_path_var, width=50).grid(row=0, column=1, **padding)
    tk.Button(root, text="Browse...", command=browse_pdf).grid(row=0, column=2, **padding)

    # Row 1: Search Text
    tk.Label(root, text="Search Text:").grid(row=1, column=0, sticky="e", **padding)
    tk.Entry(root, textvariable=search_text_var, width=50).grid(row=1, column=1, **padding)

    # Row 2: Output Folder
    tk.Label(root, text="Output Folder:").grid(row=2, column=0, sticky="e", **padding)
    tk.Entry(root, textvariable=output_dir_var, width=50).grid(row=2, column=1, **padding)
    tk.Button(root, text="Choose...", command=choose_folder).grid(row=2, column=2, **padding)

    # Row 3: Process Button
    btn_process = tk.Button(root, text="Start Processing", command=start_processing, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
    btn_process.grid(row=3, column=0, columnspan=3, pady=(15, 5))

    # Row 4: Progress Bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=5)

    # Row 5: Status Label
    lbl_status = tk.Label(root, text="Status: Idle", fg="gray")
    lbl_status.grid(row=5, column=0, columnspan=3, pady=(0, 10))

    # --- CLOSE SPLASH SCREEN ---
    # If running as a PyInstaller executable with a splash screen, close it now that the GUI is ready.
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass

    # Start the GUI loop
    root.mainloop()

if __name__ == "__main__":
    run_gui()