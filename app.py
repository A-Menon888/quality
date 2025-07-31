import streamlit as st
import asyncio
from qa_bot import ask_bot
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Configure Streamlit page
st.set_page_config(
    page_title="Quality Assurance Assistant",
    page_icon="🎯",
    layout="wide"
)

# Initialize embeddings model (do this once)
@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

embeddings = get_embeddings()

# Helper functions for uploaded PDF
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

def build_temp_faiss(text, embeddings):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.create_documents([text])
    # Add metadata to each doc chunk
    for i, doc in enumerate(docs):
        doc.metadata = {"source": f"Uploaded PDF Page Chunk {i+1}"}
    return FAISS.from_documents(docs, embeddings)

# Session state for chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Title
st.title("🎯 Quality Assurance Assistant")
st.markdown("---")

# Sidebar for file upload and context
with st.sidebar:
    st.markdown("### 💬 Chat with a Document")
    uploaded_file = st.file_uploader("Upload a PDF to analyze", type=["pdf"])
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("""
    Ask about:
    - Control charts
    - Root cause analysis
    - SOPs and audit steps
    - Defect classification
    """)
    st.markdown("### ℹ️ About")
    st.success("""
    This chatbot:
    - Uses Gemini + RAG
    - Recommends QC tools
    - Supports document-based answers
    """)
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Ask about QA tools, methods, SOPs..."):
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            custom_index = None
            if uploaded_file is not None:
                pdf_text = extract_text_from_pdf(uploaded_file)
                custom_index = build_temp_faiss(pdf_text, embeddings)
            
            response = asyncio.run(ask_bot(user_input, chat_history=st.session_state.messages, custom_index=custom_index))
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

