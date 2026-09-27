#reading pdf file with the help of pypdf library

from pypdf import PdfReader
reader = PdfReader("/Users/dixitdhiman/Downloads/my resume/Dixit Resume.pdf")
text =""

for page in reader.pages:
    text += page.extract_text()
    
print(repr(text))

