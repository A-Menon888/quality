from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from load_docs import extract_text_from_pdfs

def build_faiss_index():
    docs = extract_text_from_pdfs("pdf/")  # folder of your SOPs etc.

    texts = [d["content"] for d in docs]
    metadata = [{"source": d["filename"]} for d in docs]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.create_documents(texts, metadatas=metadata)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local("vector_index")

if __name__ == "__main__":
    build_faiss_index()
