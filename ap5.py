import streamlit as st
import fitz  # PyMuPDF
from docx import Document
import speech_recognition as sr
import preprocess as pp
import model as md
import shelve
import time
import base64
from textblob import TextBlob
from PIL import Image

st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:", layout="wide")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Load chat history from shelve file
def load_history(name="chat_history"):
    with shelve.open(name) as db:
        return db.get("messages", [])

# Save chat history to shelve file
def save_history(messages, name="chat_history"):
    with shelve.open(name) as db:
        db["messages"] = messages

# To preview pdf file type
def preview_pdf(file):
    file.seek(0)  # Ensure the file pointer is at the beginning
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="850" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# To preview doc.x file type
def preview_docx(file):
    doc = Document(file)
    paragraphs = [p.text for p in doc.paragraphs]
    preview_text = "\n".join(paragraphs)
    st.text_area(file.name, preview_text, height=600)

# To preview text file type
def preview_txt(file):
    content = file.read().decode("utf-8")
    st.text_area(file.name, content, height=600)
    
# To preview image file type
def preview_image(file):
    image = Image.open(file)
    st.image(image, caption=file.name)
    
    
def handle_sidebar():
    st.sidebar.subheader("Your documents")
    docs_collection = st.sidebar.file_uploader("Upload your documents here", accept_multiple_files=True, type=["pdf", "docx", "txt", "md", "jpeg", "jpg", "png"])

    valid_docs = []
    invalid_docs = []
    for file in docs_collection:
        if pp.validate_file_type(file):
            valid_docs.append(file)
        else:
            invalid_docs.append(file.name)

    if invalid_docs:
        st.sidebar.error(f"The following files are invalid: {', '.join([file for file in invalid_docs])}")
        st.stop()
        
    # Reset processed state if new documents are uploaded
    #if valid_docs:
    #    st.session_state.processed = False


    if valid_docs and st.sidebar.button("Process", use_container_width=True):
        with st.spinner("Processing..."):
            st.session_state.rawtext = pp.preprocess_document(docs_collection)
            st.session_state.processed = True
            for file in valid_docs:
                file.seek(0)  # Reset file pointer after processing
        show_notification("Documents processed successfully!")

    if st.sidebar.button("Delete Chat History", use_container_width=True):
        st.session_state.messages = []
        save_history([])
        show_notification("Chat history has been deleted.")

    if st.sidebar.button("Start New Chat", use_container_width=True):
        start_new_chat()
        show_notification("New chat started. Old chat history stored!", type='success')

    if st.sidebar.button("Show Old Chat History", use_container_width=True):
        st.session_state.messages = load_history(name="old_chat_history")
        show_notification("Old chat history restored!", type='success')
       
    return valid_docs

def start_new_chat():
    save_history(st.session_state.messages, name="old_chat_history")
    st.session_state.messages = []
    st.session_state.rawtext = []
    st.session_state.processed = False

def show_notification(message, type='info'):
    notification_placeholder = st.empty()
    notification_placeholder.markdown(f'<div style="position: fixed; top: 30px; right: 30px; padding: 0.5rem 1rem; margin: 20; background-color: {"#f63366" if type == "error" else "#00A36C"}; color: white; font-weight: bold; border-radius: 5px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); z-index: 999;">{message}</div>', unsafe_allow_html=True)
    time.sleep(3)
    notification_placeholder.empty()
    
# Check spelling of user input
def check_spelling(user_input):
    blob = TextBlob(user_input)
    corrected_text = str(blob.correct())
    
    if user_input != corrected_text:
        st.markdown(f"You had entered: {user_input}. Did you mean: {corrected_text}?")
    else:
        st.markdown(user_input)

def main():
    st.title("PDFs Chatbot Interface :books:")
    st.markdown("This is a chatbot interface that allows you to upload PDFs and ask questions about them.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = load_history()
    
    if "rawtext" not in st.session_state:
        st.session_state.rawtext = []

    if "recording" not in st.session_state:
        st.session_state.recording = False
        
    # Only preview the document if user click "process" button  
    if "processed" not in st.session_state:
        st.session_state.processed = False

    valid_docs = handle_sidebar()

    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.session_state.processed and valid_docs:
            st.subheader("Document Viewer")
            doc_names = [file.name for file in valid_docs]
            selected_doc = st.selectbox("Select a document to preview", doc_names)
            selected_file = next(file for file in valid_docs if file.name == selected_doc)
            if selected_file.type == "application/pdf":
                preview_pdf(selected_file)
            elif selected_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                preview_docx(selected_file)
            elif selected_file.type in ["text/plain", "text/markdown"]:
                preview_txt(selected_file)
            elif selected_file.type in ["image/jpeg", "image/png"]:
                preview_image(selected_file)
        # else:
        #     st.subheader("Please process the documents to view them here.")

    with col2:
        st.subheader("Chat")
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)

        for message in st.session_state.messages:
            avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)

        if prompt := st.chat_input("How can I help?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(prompt)
                check_spelling(prompt)
                
        response = None

        if prompt:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                with st.spinner("Thinking..."):
                    if st.session_state.rawtext:
                        response, mode = md.model(prompt, st.session_state.rawtext)
                        if mode == 'summarizer':
                            response = ' '.join([sentence['summary_text'] for sentence in response])
                        else:
                            response = response['answer']
                        response = pp.post_process(response)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "Please upload PDFs before asking questions!"
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

        if st.session_state.messages == []:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                response = "Hello! I am here to help you with your questions."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
        st.markdown('</div>', unsafe_allow_html=True)

        if prompt := st.button("Start Speech Recognition"):
            st.session_state.recording = True
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.write("Say something...")
                audio = recognizer.listen(source)

            try:
                user_input = recognizer.recognize_google(audio)
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user", avatar=USER_AVATAR):
                    st.markdown(user_input)

                if st.session_state.rawtext:
                    response, mode = md.model(user_input, st.session_state.rawtext)
                    if mode == 'summarizer':
                        response = ' '.join([sentence['summary_text'] for sentence in response])
                    else:
                        response = response['answer']
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant", avatar=BOT_AVATAR):
                        st.markdown(response)
                else:
                    show_notification("Please upload PDFs before asking questions!", type='error')

                save_history(st.session_state.messages)

            except sr.UnknownValueError:
                st.error("Sorry, could not understand audio.")
            except sr.RequestError as e:
                st.error("Could not request results; {0}".format(e))
            finally:
                st.session_state.recording = False

        if st.session_state.recording:
            if st.button("Stop Speech Recognition"):
                st.session_state.recording = False

        save_history(st.session_state.messages)

if __name__ == '__main__':
    main()
