import streamlit as st
import asyncio
from qa_bot import ask_bot

# Configure the Streamlit page
st.set_page_config(
    page_title="Quality Assurance Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextInput {
        margin-bottom: 1rem;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .tool-box {
        background-color: #e1f5fe;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .source-box {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# Main title with emoji
st.title("🎯 Quality Assurance Assistant")
st.markdown("---")

# Create two columns for a better layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Ask a Question")
    st.markdown("Get instant answers about quality processes, tools, and best practices.")
    
    # Query input with a better placeholder
    query = st.text_input(
        "",  # Label hidden for cleaner look
        placeholder="Example: What are the key steps in quality assurance testing?",
        key="query_input"
    )

    if query:
        with st.spinner('Analyzing your question...'):
            # Run the async function
            response = asyncio.run(ask_bot(query))
            
            # Split response into main content and sources
            main_content = response
            sources_section = ""
            
            if "\n\nSources:" in response:
                main_content, sources_section = response.split("\n\nSources:", 1)
            
            # Display main content
            st.markdown("<div class='response-box'>", unsafe_allow_html=True)
            st.markdown(main_content)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display sources if available
            if sources_section:
                with st.expander("View Sources"):
                    st.markdown("<div class='source-box'>", unsafe_allow_html=True)
                    st.markdown(f"Sources:{sources_section}")
                    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("### Tips")
    st.info("""
    **Try asking about:**
    - Quality tools and when to use them
    - Process improvement methods
    - Quality control procedures
    - Testing methodologies
    - Best practices in QA
    """)
    
    st.markdown("### About")
    st.success("""
    This assistant uses:
    - Advanced semantic search
    - Quality tool recommendations
    - Citations from reliable sources
    - Real-time processing
    """)

# Footer
st.markdown("---")
st.markdown(
    "💡 *The assistant provides recommendations based on industry standards and best practices in quality assurance.*",
    help="Responses are generated using context from quality management documents and industry-standard tools."
)
