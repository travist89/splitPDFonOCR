======================
 OCR PDF SPLITTER
======================

This document contains two main sections:
1. Instructions for non-technical users on how to run the pre-built application.
2. Instructions for developers on how to set up the environment and build the application from source.

-----------------------------------
 SECTION 1: FOR END-USERS (Using the .exe)
-----------------------------------

1.  Place the PDF file you want to process into the same folder as the `splitter.exe` application.
2.  Double-click `splitter.exe` to run it.
3.  A console window will appear asking for three pieces of information. You can press Enter to accept the default values shown in parentheses.
    -   **PDF file name**: (default: example.pdf) - Type the name of your PDF file.
    -   **Search text**: (default: Employee Number:) - This is the text the app looks for to start a new section.
    -   **Output directory**: (default: output) - This is the folder where the split files will be saved.
4.  The program will process the PDF page by page. When it is finished, you will see a "SUCCESS" message.
5.  Check the `output` folder for your split PDF files.


-----------------------------------
 SECTION 2: FOR DEVELOPERS
-----------------------------------

### PART A: Initial Environment Setup
1.  **Install Required Software:**
    -   **Python:** Install from python.org or the Microsoft Store. Ensure it's added to your PATH.
    -   **Poppler:** Download the latest Windows release and unzip it. You do not need to add it to your system PATH if you plan to bundle it with PyInstaller.
        (https://github.com/oschwartz10612/poppler-windows/releases)
    -   **Tesseract-OCR:** Install from the official downloads page.
        (https://tesseract-ocr.github.io/tessdoc/Downloads.html)

2.  **Create Python Virtual Environment:**
    Open a terminal in the project directory and run:
    `python -m venv venv`

3.  **Activate Virtual Environment:**
    `.\venv\scripts\activate`

4.  **Install Dependencies:**
    `pip install -r requirements.txt`

### PART B: Running the Script Directly
1.  Activate the virtual environment (`.\venv\scripts\activate`).
2.  Run the script: `python splitter.py`
3.  Follow the interactive prompts in the console.

### PART C: Building the Standalone Executable
This process bundles the script, Python interpreter, and all dependencies (including Poppler and Tesseract) into a single `.exe` file for easy distribution.

1.  Activate the virtual environment.
2.  Run the PyInstaller command below.
    **IMPORTANT:** You MUST replace the example paths for Poppler and Tesseract with the actual paths on your machine. To find a path, locate the folder in File Explorer and copy it from the address bar.

    ```
    pyinstaller --clean --onefile --noconsole --icon=top.ico --splash=top.jpg --add-data "top.ico;." --add-data "C:\poppler-24.02.0\Library\bin;Poppler\Library\bin" --add-data "C:\Program Files\Tesseract-OCR;Tesseract-OCR" splitter.py
    ```

3.  The final `splitter.exe` will be located in the `dist` folder. It will be large but is fully self-contained and portable.