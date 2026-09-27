#reading pdf file with the help of pypdf library

from pypdf import PdfReader

default_path = "/Users/dixitdhiman/Downloads/my resume/Dixit Resume.pdf"

def read_pdf(file_path=default_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text

resume_text = read_pdf()
print(resume_text)

