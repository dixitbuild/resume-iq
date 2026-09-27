
import unicodedata


def clean(text: str) -> str:
    """
    Cleans the input text by removing unwanted characters and formatting.

    Args:
        text (str): The input text to be cleaned.   
    """
    cleaned_text = ''
    for char in text:
        if char =='+' or char == '\n' or unicodedata.category(char)[0] in ['L', 'N', 'P', 'Z']:
            cleaned_text += char
   
    return cleaned_text