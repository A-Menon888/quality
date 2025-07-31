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
model = genai.GenerativeModel("gemini-2.5-flash-lite")
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

async def ask_bot(query, chat_history=None, custom_index=None):
    # Initialize vector store if not already done
    if vector_store is None and custom_index is None:
        initialize_vector_store()

    # Use the custom index if provided, otherwise use the default vector store
    db = custom_index if custom_index else vector_store
    
    # Run tool recommendation in parallel
    loop = asyncio.get_event_loop()
    tool_future = loop.run_in_executor(executor, get_tool_recommendation, query)

    # Get relevant documents from vector DB
    relevant_docs = db.similarity_search(query, k=3)

    # Prepare context with source citations
    context_with_sources = []
    source_map = {}

    for i, doc in enumerate(relevant_docs, 1):
        source = doc.metadata.get('source', 'Uploaded Document')
        source_id = f"[{i}]"
        source_map[source_id] = source
        context_with_sources.append(f"{doc.page_content} {source_id}")

    doc_context = "\n\n".join(context_with_sources)

    # Format memory (last 2–3 exchanges)
    memory_context = ""
    if chat_history:
        for msg in chat_history[-10:]:  # Last 5 rounds
            role = "User" if msg["role"] == "user" else "Assistant"
            memory_context += f"{role}: {msg['content']}\n"

    # Final prompt
    prompt = f"""
You are a quality assurance assistant. Use the following SOP context and recent conversation to answer the user's latest question.
Include citations [n] when referencing document content.

Recent Conversation:
{memory_context}

Document Context:
{doc_context}

Current Question:
{query}

Your response should:
1. Directly address the question
2. Reference sources using [n] notation when relevant
3. Recommend quality tools where applicable
4. Be concise, helpful, and well-organized
"""

    # Wait for tool recommendation to finish
    tool_recommendation = await tool_future

    # Generate answer from Gemini
    response = model.generate_content(prompt)
    answer = response.text.strip() + tool_recommendation

    # Add citation list
    if source_map:
        sources_section = "\n\nSources:"
        for source_id, source in source_map.items():
            # For uploaded files, the source might not be a path
            if isinstance(source, str):
                sources_section += f"\n{source_id} {os.path.basename(source)}"
            else:
                 sources_section += f"\n{source_id} Uploaded Document"
        answer += sources_section

    return answer


