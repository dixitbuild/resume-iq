#reading pdf file with the help of pypdf library

from pypdf import PdfReader
reader = PdfReader("/Users/dixitdhiman/Downloads/my resume/Dixit Resume.pdf")
text = reader.pages[0].extract_text()
print(repr(text))

