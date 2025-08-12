import sys
import os
import subprocess
import pypdf
from tqdm import tqdm

THRESHOLD = 52  # Character count threshold to determine if OCR is needed

def analyze_pdf_pages(file_path):
    """
    Analyzes a PDF file to identify pages with and without a text layer.

    Args:
        file_path (str): The path to the PDF file.
    
    Returns:
        list: A list of page numbers that likely need OCR.
    """        
    try:
        pdf_reader = pypdf.PdfReader(file_path)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return []

    num_pages = len(pdf_reader.pages)
    print(f"Analyzing '{file_path}' ({num_pages} pages)...")

    pages_needing_ocr = []
    char_counts= []

    # Use tqdm for a progress bar
    for i in tqdm(range(num_pages), desc="Checking pages"):
        page = pdf_reader.pages[i]
        # Extract text. If the result is empty or only whitespace, it needs OCR.
        text = page.extract_text().strip()
        
        # A simple heuristic: if the extracted text is very short,
        # it's likely a scanned page with no searchable text.
        # The threshold of 32 characters is a good starting point but can be adjusted.
        char_counts.append(f"Page {i + 1}: {len(text)}")
        if len(text) <= THRESHOLD:
            pages_needing_ocr.append(i + 1) # Page numbers are 1-based

    print("\n--- Analysis Complete ---")
    print("Character counts per page:")
    for count in char_counts:
        print(count)
    if pages_needing_ocr:
        print(f"Found {len(pages_needing_ocr)} pages that likely need OCR.")
    else:
        print("Found no pages that need OCR. The document appears to be fully searchable.")
    print("-------------------------")
    
    return pages_needing_ocr

def run_ocr_for_file(input_file, output_folder, pages_to_ocr):
    """
    Runs ocrmypdf on a file for the specified pages.

    Args:
        input_file (str): The path to the input PDF file.
        output_folder (str): The folder to save the OCR'd file.
        pages_to_ocr (list): A list of page numbers to perform OCR on.
    """
    if not pages_to_ocr:
        print(f"No pages to OCR for {input_file}. Skipping OCR step.")
        return
        
    # Get the base filename to create the output path
    filename = os.path.basename(input_file)
    output_file = os.path.join(output_folder, filename)

    pages_arg = ",".join(map(str, pages_to_ocr))

    command = [
        'ocrmypdf',
        '-l', 'ell+eng+tur',  # Specify languages
        '--redo-ocr',         # Force OCR on the selected pages
        '--pages', pages_arg,
        input_file,
        output_file
    ]

    print(f"Running command for {filename} on pages: {pages_arg}")
    try:
        subprocess.run(command, check=True)
        print(f"OCR completed successfully for {filename}.")
    except subprocess.CalledProcessError as e:
        print(f"ocrmypdf failed for {filename} with error: {e}")
    except FileNotFoundError:
        print("ocrmypdf command not found. Please ensure it's installed and in your PATH.")

def process_folder(source_folder, output_folder):
    """
    Processes all PDF files in a source folder, checks them, and runs OCR.

    Args:
        source_folder (str): The folder containing the PDF files to process.
        output_folder (str): The folder to save the OCR'd files.
    """
    if not os.path.isdir(source_folder):
        print(f"Error: Source folder '{source_folder}' does not exist.")
        return
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: '{output_folder}'")

    # List all PDF files in the source folder
    file_list = [f for f in os.listdir(source_folder) if f.endswith('.pdf')]
    
    if not file_list:
        print(f"No PDF files found in '{source_folder}'.")
        return

    print(f"Found {len(file_list)} PDF files to process.")
    print("-" * 30)

    for filename in file_list:
        # if not filename.lower().endswith('tome 2.pdf'):
        #     continue

        file_path = os.path.join(source_folder, filename)
        
        # 1. Open and analyze the file
        pages_to_ocr = analyze_pdf_pages(file_path)
        
        # 2. Run ocrmypdf if necessary
        run_ocr_for_file(file_path, output_folder, pages_to_ocr)
        
        print("-" * 30)


if __name__ == "__main__":
    # Define source and output folders
    source_dir = "archive"
    output_dir = "ocr"

    process_folder(source_dir, output_dir)
