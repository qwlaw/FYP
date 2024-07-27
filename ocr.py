import streamlit as st
import pytesseract
from PIL import Image
import io

def perform_ocr_main(file):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\ASUS\Documents\tesseract.exe"
    image = Image.open(file)
    #st.image(image, caption='Uploaded Image.', use_column_width=True)
    #st.write("")
    #st.write("Performing OCR...")

    try:
        text = pytesseract.image_to_string(image)

        return text
    except Exception as e:
        return str(e)

    finally:
        st.write("Performed OCR!")
        # st.write("Extracted Text:")
        # st.write(text)
