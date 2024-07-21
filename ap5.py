import preprocess as pp
import streamlit as st
import model as md
import shelve
import time
from textblob import TextBlob

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Load chat history from a shelve file
def load_history(name="chat_history"):
    with shelve.open(name) as db:
        return db.get("messages", [])

# Save chat history to a shelve file
def save_history(messages, name="chat_history"):
    with shelve.open(name) as db:
        db["messages"] = messages

# Handle file uploads in the sidebar
def handle_sidebar():
    docs_collection = st.file_uploader("Upload your documents here", accept_multiple_files=True, type=["pdf", "docx", "txt", "md", "jpeg", "jpg", "png"])
    
    # Validate uploaded files
    valid_docs = [file for file in docs_collection if pp.validate_file_type(file)]
    invalid_docs = [file.name for file in docs_collection if not pp.validate_file_type(file)]

    if invalid_docs:
        st.error(f"The following files are invalid: {', '.join(invalid_docs)}")
        st.stop()  # Stop execution if there are invalid files

    return docs_collection, valid_docs

# Start a new chat by clearing the current history
def start_new_chat():
    save_history(st.session_state.messages, name="old_chat_history")
    st.session_state.messages = []
    st.session_state.rawtext = []

# Show notifications to the user
def show_notification(message, type='info'):
    notification_placeholder = st.empty()
    color = "#f63366" if type == "error" else "#00A36C"
    notification_placeholder.markdown(
        f'<div style="position: fixed; top: 30px; right: 30px; padding: 0.5rem 1rem; background-color: {color}; color: white; font-weight: bold; border-radius: 5px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); z-index: 999;">{message}</div>', 
        unsafe_allow_html=True
    )
    time.sleep(3)
    notification_placeholder.empty()

# Initialize or load chat history
def chat_history():
    if "messages" not in st.session_state: 
        st.session_state.messages = load_history()

    if "rawtext" not in st.session_state:
        st.session_state.rawtext = []

# Process user input and generate a response
def process_user_input(user_input):
    response = None
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Thinking..."):
            if user_input and st.session_state.rawtext:
                response, mode = md.model(user_input, st.session_state.rawtext)
                if mode == 'summarizer':
                    response = ' '.join([sentence['summary_text'] for sentence in response])
                else:
                    response = response['answer']
                st.markdown(response)
            elif not st.session_state.rawtext:
                show_notification("Please upload PDFs before asking questions!", type='error')
    return response

# Sidebar setup
def sidebar():
    with st.sidebar:
        st.subheader("Your documents")
        docs_collection, valid_docs = handle_sidebar()
    
        if valid_docs and st.button("Process", use_container_width=True):
            with st.spinner("Processing..."):
                st.session_state.rawtext = pp.preprocess_document(docs_collection)  
                show_notification("Documents processed successfully!")

        if st.button("Delete Chat History", use_container_width=True):
            st.session_state.messages = []
            save_history([])
            show_notification("Chat history has been deleted.")
            
        if st.button("Start New Chat", use_container_width=True):
            start_new_chat()
            show_notification("New chat started. Old chat history stored!", type='success')
        
        if st.button("Show Old Chat History", use_container_width=True):
            show_notification("Old chat history restored!", type='success')
            st.session_state.messages = load_history(name="old_chat_history")

# Check spelling of user input
def check_spelling(user_input):
    blob = TextBlob(user_input)
    corrected_text = str(blob.correct())
    
    if user_input != corrected_text:
        st.markdown(f"You had entered: {user_input}. Did you mean: {corrected_text}?")
    else:
        st.markdown(user_input)

# Main application logic
def main():

    
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.title("PDFs Chatbot Interface :books:")
    st.markdown("This is a chatbot interface that allows you to upload PDFs and ask questions about them.")

    chat_history()
    sidebar()

    # Display chat messages
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            
    # Main chat interface
    if prompt := st.chat_input("How can I help?"):
        st.session_state.messages.append({"role": "user", "content": prompt})  
        with st.chat_message("user", avatar=USER_AVATAR):
            check_spelling(prompt)
        
        response = process_user_input(prompt)

        if response is not None:
            st.session_state.messages.append({"role": "assistant", "content": response})

    save_history(st.session_state.messages)

if __name__ == '__main__':
    main()
