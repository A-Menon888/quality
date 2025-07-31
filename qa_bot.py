import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
from tool_recommender import check_for_tool

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ask_bot(query):
    tool_match = check_for_tool(query)
    if tool_match["match"]:
        return f"Recommended Tool: **{tool_match['tool']}**\nWhen to Use: {tool_match['when_to_use']}"

    # Load FAISS vector index
    db = FAISS.load_local(
    "vector_index", 
    HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    allow_dangerous_deserialization=True  # Add this line
    )
    retriever = db.as_retriever()
    
    # Retrieve top 3 relevant chunks
    relevant_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in relevant_docs[:3]])

    prompt = f"""
You are a quality assurance assistant. Use the following context from SOPs and QC manuals to answer the user question. Recommend a tool.

Context:
{context}

Question:
{query}

Answer:"""

    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content(prompt)
    return response.text

# Example
if __name__ == "__main__":
    print(ask_bot("What is IBM's approach to bad quality products?"))
