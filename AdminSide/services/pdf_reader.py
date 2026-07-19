from pypdf import PdfReader


def extract_pdf_text(pdf_file):
    
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        extracted_text = page.extract_text()

        if extracted_text:
            text += extracted_text + "/n"

    return text

