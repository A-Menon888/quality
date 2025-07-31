import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
from tool_recommender import check_for_tool
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize global resources
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = None
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
executor = ThreadPoolExecutor(max_workers=3)  # For parallel operations

def initialize_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = FAISS.load_local(
            "vector_index",
            embeddings,
            allow_dangerous_deserialization=True
        )

# Cache tool recommendations to avoid recomputing for similar queries
@lru_cache(maxsize=1000)
def get_tool_recommendation(query):
    tool_match = check_for_tool(query)
    if tool_match["match"]:
        confidence = tool_match.get("confidence", 0) * 100
        return f"\n\nRecommended Quality Tool: **{tool_match['tool']}** (Confidence: {confidence:.1f}%)\n{tool_match['when_to_use']}"
    return ""

async def ask_bot(query):
    # Initialize vector store if not already done
    if vector_store is None:
        initialize_vector_store()
    
    # Run tool recommendation and document retrieval in parallel
    loop = asyncio.get_event_loop()
    tool_future = loop.run_in_executor(executor, get_tool_recommendation, query)
    
    # Get relevant documents
    relevant_docs = vector_store.similarity_search(query, k=3)

    # Load FAISS vector index for context
    db = FAISS.load_local(
        "vector_index", 
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
        allow_dangerous_deserialization=True
    )
    retriever = db.as_retriever()
    
    # Prepare context with source information
    context_with_sources = []
    source_map = {}
    
    for i, doc in enumerate(relevant_docs, 1):
        source = doc.metadata.get('source', 'Unknown Source')
        source_id = f"[{i}]"
        source_map[source_id] = source
        context_with_sources.append(f"{doc.page_content} {source_id}")
    
    context = "\n\n".join(context_with_sources)

    prompt = f"""
You are a quality assurance assistant. Use the following context from SOPs and QC manuals to answer the user question.
The context includes source citations in [n] format. Include these citations in your answer when referencing specific information.

Context:
{context}

Question:
{query}

Provide a clear and concise answer that:
1. Directly addresses the question
2. Uses citations [n] when referencing specific information from the context
3. Explains any recommended quality tools and why they would be helpful
4. Synthesizes information from multiple sources when relevant"""

    # Get tool recommendation result from parallel execution
    tool_recommendation = await tool_future
    
    # Generate response
    response = model.generate_content(prompt)
    
    # Combine results
    answer = response.text + tool_recommendation
    
    # Add sources section
    if source_map:
        sources_section = "\n\nSources:"
        for source_id, source in source_map.items():
            sources_section += f"\n{source_id} {os.path.basename(source)}"
        answer += sources_section
        
    return answer

# Example
if __name__ == "__main__":
    async def main():
        response = await ask_bot("What are the key steps in quality assurance testing?")
        print(response)
    
    asyncio.run(main())