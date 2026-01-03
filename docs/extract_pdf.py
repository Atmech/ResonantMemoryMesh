import sys
try:
    import pypdf
except ImportError:
    # prompt to install
    print("pypdf not installed")
    sys.exit(1)

def extract_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(f"--- START OF {pdf_path} ---")
        print(text)
        print(f"--- END OF {pdf_path} ---")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

if __name__ == "__main__":
    for path in sys.argv[1:]:
        extract_text(path)
