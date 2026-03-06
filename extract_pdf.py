import sys
try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf not installed. Please install it with: pip install pypdf")
    sys.exit(1)

def extract_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            print(f"\n--- PAGE {i+1} ---")
            print(page.extract_text())
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf.py <pdf_path>")
        sys.exit(1)
    extract_text(sys.argv[1])
