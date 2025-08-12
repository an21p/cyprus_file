import os
import subprocess
import multiprocessing
from functools import partial

# --- Configuration ---
# Set the directory to scan for PDF files. Use "." for the current directory.
SOURCE_DIRECTORY = "archive"
OUTPUT_DIRECTORY = "ocr"

# Languages for OCR. Add more with a '+' separator, e.g., "eng+ell+tur+fra"
LANGUAGES = "eng+ell+tur"

# Suffix to add to the processed files. Input: "Tome 1.pdf" -> Output: "Tome 1_ocr.pdf"
OUTPUT_SUFFIX = "_ocr"

# --- End of Configuration ---

def run_ocr_on_file(input_file, source_dir, output_dir, languages, suffix):
    """
    Worker function to run OCR on a single PDF file.
    This function is executed by each parallel process.
    """
    # Construct the full path for the output file
    filename_without_ext = os.path.splitext(input_file)[0]
    output_file = f"{filename_without_ext}{suffix}.pdf"

    input_path = os.path.join(source_dir, input_file)
    output_path = os.path.join(output_dir, output_file)

    # Get the process ID for logging purposes
    pid = os.getpid()

    print(f"[Process {pid}] STARTING: OCR for '{input_file}'")

    # Build the ocrmypdf command as a list of arguments
    command = [
        "ocrmypdf",
        "-l", languages,
        "--force-ocr",
        input_path,
        output_path,
    ]

    try:
        # Execute the command
        result = subprocess.run(
            command,
            check=True,       # Raise an exception if the command returns a non-zero exit code
            capture_output=True,
            text=True         # Capture stdout/stderr as text
        )
        print(f"[Process {pid}] SUCCESS: Created '{output_file}'")
        return None # Return None on success
    except FileNotFoundError:
        # This error occurs if `ocrmypdf` is not installed or not in the system's PATH
        return f"[Process {pid}] FATAL ERROR: The 'ocrmypdf' command was not found. Please ensure it is installed and accessible in your system's PATH."
    except subprocess.CalledProcessError as e:
        # This error occurs if ocrmypdf returns an error
        error_message = f"""
        [Process {pid}] FAILED to process '{input_file}'.
        ocrmypdf returned an error (exit code {e.returncode}).
        --- OCRmyPDF Error Output ---
        {e.stderr.strip()}
        -----------------------------
        """
        return error_message


def main():
    # Find all PDF files in the source directory that have not been processed yet
    try:
        all_files = os.listdir(SOURCE_DIRECTORY)
    except FileNotFoundError:
        print(f"Error: The directory '{SOURCE_DIRECTORY}' was not found.")
        return

    files_to_process = [
        f for f in all_files
        if f.lower().endswith(".pdf") and not f.lower().endswith(f"{OUTPUT_SUFFIX}.pdf")
    ]

    if not files_to_process:
        print("No new PDF files to process found.")
        return

    print(f"Found {len(files_to_process)} PDF file(s) to process:")
    for f in files_to_process:
        print(f"  - {f}")
        partial(
        run_ocr_on_file,
        source_dir=SOURCE_DIRECTORY,
        output_dir=OUTPUT_DIRECTORY,
        languages=LANGUAGES,
        suffix=OUTPUT_SUFFIX
        )
    print("-" * 40)


if __name__ == "__main__":
    # This check is important for multiprocessing to work correctly on all platforms
    main()
