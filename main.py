from ingestion.parsers import read_pdf
from ingestion.cleaners import clean

resume_text = read_pdf()
cleaned_text = clean(resume_text)
print(cleaned_text)