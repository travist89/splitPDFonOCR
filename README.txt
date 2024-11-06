OCR PDF SPLITTER

SETUP:
1. Make sure you have Python installed on your PC and your PATH environment variable is set 
2. Create a new Virtual Environment on your PC. 
    python -m venv venv
3. Activate the venv
    .\venv\scripts\activate
4. Install the dependencies from requirements.txt
    pip install -r requirements.txt

HOW TO USE:
1. Place the PDF you want to split in the root of the app directory and name it example.pdf
    ex: "C:\Users\tthompson\splitPDFonOCR\example.pdf"
2. From within your activated venv, call the script.
    python .\splitter.py
3. Wait for it to finish, then check the output directory
    ex: "C:\Users\tthompson\splitPDFonOCR\output"


