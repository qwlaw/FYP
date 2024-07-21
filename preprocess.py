from langchain.text_splitter import CharacterTextSplitter
from nltk.tokenize import word_tokenize 
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
from docx import Document
import markdown
import re
import ocr

# import nltk
# nltk.download('stopwords')

def get_text_chunks(raw_text):
    
    splitter = CharacterTextSplitter(
     separator=".",
     chunk_size = 2500,
     chunk_overlap = 250,
     length_function=len
    )
    text_chunks = splitter.split_text(raw_text)

    return text_chunks

def preprocess_document(docs_collection):
    processed_text = get_text_from_files(docs_collection)
    combined_text = "".join(processed_text)
    combined_text = preprocess_text(combined_text)
    return combined_text

def preprocess_text(text):

    text = text.replace("\n", " ")
    text = remove_stopwords(text)
    text = remove_url(text)
    return text

def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    
    filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
    
    filtered_sentence = []
 
    for w in word_tokens:
        if w not in stop_words:
            filtered_sentence.append(w)
            
    return " ".join(filtered_sentence)

def remove_url(text):
    return re.sub(r'http\S+', '', text)

def remove_translation_prefix(text):
  if text.startswith('='):
    return text[1:]  # Use index 1 to directly take everything after the first character
  else:
    return text

def get_text_from_files(docs_collection):
    text = ""
    for doc in docs_collection:
        file_type = doc.name.split(".")[-1].lower()
        if file_type == "pdf":
            text += read_text_from_pdf(doc)
        elif file_type == "docx":
            text += read_text_from_docx(doc)
        elif file_type == "txt":
            text += read_text_from_txt(doc)
        elif file_type == "md":
            text += read_text_from_md(doc)
        elif file_type in ["jpeg", "jpg", "png"]:
            text += read_text_from_image(doc)
    return text

def validate_file_type(file):
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.jpeg', '.jpg', '.png']
    allowed_mime_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown', 'image/jpeg', 'image/png']

    file_extension = None
    file_mime_type = None

    if file is not None:
        file_extension = '.' + file.name.split('.')[-1].lower()
        file_mime_type = file.type

    if file_extension in allowed_extensions or file_mime_type in allowed_mime_types:
        return True
    else:
        return False

# Retreive the text from the pdf files
def read_text_from_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_text_from_docx(file):
    text = ""
    doc = Document(file)
    for paragraph in doc.paragraphs:
        text += paragraph.text
    return text

def read_text_from_txt(file):
    return file.getvalue().decode("utf-8")

def read_text_from_md(file):
    return markdown.markdown(file.getvalue().decode("utf-8"))
    
def read_text_from_image(file):
    text = ocr.perform_ocr_main(file)
    return text


# Handle Post-processing of the chat messages
def post_process(messages):
    messages = capitalize_sentences(messages)
    messages = check_last_2_character(messages)
    return messages

def check_last_2_character(text):
    if text[-1].isalnum():
            text = text + "."
    else:
        if text[-1] not in ".!?":
            text = text[:-1]
            if text[-1].isalnum():
               text = text + "."
            else:
                text = text[:-1] + "."
    return text

def capitalize_sentences(input_string):
    # Split the string into sentences
    sentences = input_string.split('. ')
    
    # Capitalize the first letter of each sentence
    capitalized_sentences = [sentence.capitalize() for sentence in sentences]
    
    # Join the sentences back together
    result = '. '.join(capitalized_sentences)
    
    return result