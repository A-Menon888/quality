import streamlit as st
import asyncio
from qa_bot import ask_bot
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import io
import datetime
import textwrap
import re
from qa_bot import ask_bot_with_tool_generation, ask_bot_with_escalation, dynamic_tool_generator, tool_display, data_forms, tool_customization, export_manager, get_chart_explanation
import asyncio
from tool_recommender import check_for_tool, check_for_tool_generation, enhanced_tool_lookup
import pandas as pd
from typing import Dict, Any, List, Optional
from data_extractor import DefectData, ProcessData, CauseEffectData
st.set_page_config(
    page_title="Quality Assurance Assistant",
    page_icon="🎯",
    layout="wide"
)

# Email validation function
def is_valid_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

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
# Helper to get CSV/Excel data as string for Gemini
def get_csv_excel_context():
    df = st.session_state.get("uploaded_csv_excel_df")
    if df is not None:
        # limit rows/cols for prompt size if needed
        preview = df.head(30)
        return f"Uploaded CSV/Excel data (showing up to 30 rows):\n{preview.to_csv(index=False)}"
    return ""

# ---------- PDF Export Utilities ----------

def render_chat_to_pdf(messages, title="Quality Assurance Assistant Chat"):
    """Render chat messages to a paginated PDF and return bytes."""
    # Page setup (A4 size in points)
    page_width, page_height = 595, 842
    margin_left = 50
    margin_right = 50
    margin_top = 50
    margin_bottom = 50

    line_height = 14
    title_font_size = 16
    text_font_size = 11
    small_font_size = 9

    buffer = io.BytesIO()
    doc = fitz.open()

    def new_page(page_num: int):
        page = doc.new_page(width=page_width, height=page_height)
        y = margin_top
        # Header
        page.insert_text((margin_left, y), title, fontsize=title_font_size, fontname="helv", fill=(0, 0, 0))
        y += line_height * 2
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        page.insert_text((margin_left, y), f"Exported: {ts}", fontsize=small_font_size, fontname="helv", fill=(0, 0, 0))
        y += line_height * 1.5
        # Thin divider
        page.draw_line((margin_left, y), (page_width - margin_right, y), color=(0.7, 0.7, 0.7), width=0.5)
        y += line_height
        # Footer with page number
        footer_text = f"Page {page_num}"
        page.insert_text((page_width - margin_right - 60, page_height - margin_bottom + 10), footer_text, fontsize=small_font_size, fontname="helv", fill=(0.3, 0.3, 0.3))
        return page, y

    def write_wrapped_text(page, x, y, text, width_chars):
        nonlocal line_height
        for line in textwrap.wrap(text, width=width_chars, replace_whitespace=False, drop_whitespace=False):
            page.insert_text((x, y), line, fontsize=text_font_size, fontname="helv", fill=(0, 0, 0))
            y += line_height
        return y

    page_num = 1
    page, cursor_y = new_page(page_num)

    usable_width_chars = 90  # tuned for font size and margins

    for msg in messages:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = (msg.get("content") or "").replace("\r\n", "\n").strip()

        # Section heading for each message
        heading_text = f"{role}:"
        if cursor_y > page_height - margin_bottom - line_height * 3:
            page_num += 1
            page, cursor_y = new_page(page_num)
        page.insert_text((margin_left, cursor_y), heading_text, fontsize=text_font_size, fontname="helv", fill=(0.1, 0.1, 0.5))
        cursor_y += line_height

        # Body text wrapped
        for para in content.split("\n"):
            if not para.strip():
                cursor_y += line_height
                continue
            if cursor_y > page_height - margin_bottom - line_height * 2:
                page_num += 1
                page, cursor_y = new_page(page_num)
            cursor_y = write_wrapped_text(page, margin_left, cursor_y, para, usable_width_chars)

        # Divider between messages
        cursor_y += line_height * 0.5
        if cursor_y > page_height - margin_bottom - line_height * 2:
            page_num += 1
            page, cursor_y = new_page(page_num)
        page.draw_line((margin_left, cursor_y), (page_width - margin_right, cursor_y), color=(0.85, 0.85, 0.85), width=0.7)
        cursor_y += line_height

    doc.save(buffer)
    doc.close()
    buffer.seek(0)
    return buffer.getvalue()

# Session state for chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Title
st.title("🎯 Quality Assurance Assistant")
st.markdown("---")

# Sidebar for file upload and context
with st.sidebar:
    st.markdown("### 💬 Chat with a Document or Image")

    uploaded_file = st.file_uploader("Upload a PDF to analyze", type=["pdf"])
    uploaded_image = st.file_uploader("Upload an image (Vision mode)", type=["png", "jpg", "jpeg"], key="image_uploader")
    uploaded_csv_excel = st.file_uploader("Upload a CSV or Excel file to analyze", type=["csv", "xlsx", "xls"], key="csv_excel_uploader")

    if uploaded_csv_excel is not None:
        try:
            if uploaded_csv_excel.name.endswith('.csv'):
                df = pd.read_csv(uploaded_csv_excel)
            else:
                df = pd.read_excel(uploaded_csv_excel)

            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head())

            # Store in session state for chatbot use
            st.session_state.uploaded_csv_excel_df = df
            st.success("CSV/Excel file loaded and available for chat analysis!")

            # Select column for analysis
            if len(df.columns) > 1:
                column = st.selectbox("Select column to analyze", df.columns, key="csv_excel_column_select")
            else:
                column = df.columns[0]

            measurements = df[column].dropna().tolist()

            # Optional: run analysis
            if st.button("Analyze Uploaded Data", key="analyze_csv_excel"):
                from data_extractor import ProcessData
                process_data = ProcessData(
                    measurements=measurements,
                    specifications={},
                    sample_size=len(measurements),
                    process_name=None,
                    source="file_upload"
                )
                result = dynamic_tool_generator.generate_tool("process_capability", process_data)

                if result.success:
                    st.success("✅ Data analyzed!")
                    tool_display.display_generated_tool(
                        {
                            "success": True,
                            "chart_data": result.chart_data,
                            "statistics": result.data_summary
                        },
                        "process_capability",
                        show_statistics=True,
                        show_customization=False
                    )
                else:
                    st.error(f"❌ {result.error_message}")

        except Exception as e:
            st.error(f"Error reading or analyzing file: {str(e)}")

    image_mode = None
    if uploaded_image is not None:
        st.image(uploaded_image, caption="Preview", use_container_width=True)
        image_mode = st.radio(
            "Image handling mode",
            options=["Ask about this image"],
            index=0,
            help="Vision-only: the model will analyze the image directly."
        )

    st.markdown("---")
    # Download chat as PDF button
    if st.session_state.messages:
        pdf_bytes = render_chat_to_pdf(st.session_state.messages)
        default_name = f"qa_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            label="⬇️ Download chat as PDF",
            data=pdf_bytes,
            file_name=default_name,
            mime="application/pdf",
            help="Export the current conversation as a formatted PDF."
        )

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
    - Vision mode for images (no citations)
    - Auto-escalates uncertain responses
    """)
    
    # Escalation configuration section
    st.markdown("---")
    st.markdown("### ⚠️ Escalation Settings")
    
    # Recipient email input
    recipient_email = st.text_input(
        "📧 Recipient Email for Escalations",
        value="aayush.pmenon2023@vitstudent.ac.in",  # Default value
        help="Email address where escalation notifications will be sent"
    )
    
    # Validate email format
    if recipient_email and not is_valid_email(recipient_email):
        st.error("❌ Please enter a valid email address")
        recipient_email = None
    elif recipient_email:
        st.success(f"✅ Escalations will be sent to: {recipient_email}")
    
    # Store in session state
    if recipient_email and is_valid_email(recipient_email):
        st.session_state.recipient_email = recipient_email
    
    # Test email connection
    if st.button("🔧 Test Email Connection", help="Test if escalation email is configured correctly"):
        from email_config import EmailEscalation
        email_escalation = EmailEscalation()
        if email_escalation.test_email_connection():
            st.success("✅ Email connection successful!")
        else:
            st.error("❌ Email connection failed. Check your secrets configuration.")
    
    st.info("""
    **Escalation triggers when:**
    - Confidence < 30%
    - Response contains uncertainty phrases
    - Tool requests fail
    - Generic/unhelpful responses
    
    **Configure in Streamlit secrets:**
    - ESCALATION_EMAIL
    - ESCALATION_PASSWORD  
    - MANAGER_EMAIL
    """)
    
    # Persona selection section
    st.markdown("---")
    st.markdown("### 🎭 Chatbot Persona")
    
    # Persona selection dropdown
    persona_options = {
        "Novice Guide": {
            "description": "Explains tools simply with analogies and step-by-step guidance",
            "icon": "🌱"
        },
        "Expert Consultant": {
            "description": "Uses technical terms and advanced quality methodologies",
            "icon": "🎓"
        },
        "Skeptical Manager": {
            "description": "Challenges recommendations and asks for proof of effectiveness",
            "icon": "🤔"
        }
    }
    
    # Create persona selection with descriptions
    selected_persona = st.selectbox(
        "Choose your preferred interaction style:",
        options=list(persona_options.keys()),
        index=0,  # Default to Novice Guide
        help="Select how you'd like the chatbot to respond to your queries"
    )
    
    # Display selected persona info
    persona_info = persona_options[selected_persona]
    st.info(f"""
    **{persona_info['icon']} {selected_persona}**
    
    {persona_info['description']}
    """)
    
    # Store persona in session state
    st.session_state.selected_persona = selected_persona
    
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    # Add tool generation section to sidebar
    st.markdown("---")
    st.markdown("### ��️ Tool Generation")
    
    # Quick tool generation buttons
    if st.button("📊 Generate Pareto Chart", help="Click to manually create a Pareto chart"):
        st.session_state.show_data_form = "pareto"
        st.rerun()
    
    if st.button("�� Generate Fishbone Diagram", help="Click to manually create a Fishbone diagram"):
        st.session_state.show_data_form = "fishbone"
        st.rerun()
    
    if st.button("📈 Generate Control Chart", help="Click to manually create a control chart"):
        st.session_state.show_data_form = "control_chart"
        st.rerun()
    
    if st.button("📊 Generate Histogram", help="Click to manually create a histogram"):
        st.session_state.show_data_form = "histogram"
        st.rerun()
    
    if st.button("⚙️ Generate Capability Analysis", help="Click to manually create a process capability analysis"):
        st.session_state.show_data_form = "process_capability"
        st.rerun()
    
    # Data input forms
    if hasattr(st.session_state, 'show_data_form') and st.session_state.show_data_form:
        st.markdown("---")
        st.markdown("### 📝 Data Input")
        
        if st.session_state.show_data_form == "pareto":
            defect_data = data_forms.defect_data_form()
            if defect_data:
                if st.button("Generate Pareto Chart", key="gen_pareto"):
                    try:
                        result = dynamic_tool_generator.generate_tool("pareto_chart", defect_data)
                        if result.success:
                            st.success("✅ Pareto Chart Generated!")
                            tool_display.display_generated_tool(
                                {
                                    "success": True,
                                    "chart_data": result.chart_data,
                                    "statistics": result.data_summary
                                },
                                "pareto_chart",
                                show_statistics=False,
                                show_customization=False
                            )
                        else:
                            st.error(f"❌ {result.error_message}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        elif st.session_state.show_data_form == "fishbone":
            cause_data = data_forms.cause_effect_data_form()
            if cause_data:
                if st.button("Generate Fishbone Diagram", key="gen_fishbone"):
                    try:
                        result = dynamic_tool_generator.generate_tool("fishbone_diagram", cause_data)
                        if result.success:
                            st.success("✅ Fishbone Diagram Generated!")
                            tool_display.display_generated_tool(
                                {
                                    "success": True,
                                    "chart_data": result.chart_data,
                                    "statistics": result.data_summary
                                },
                                "fishbone_diagram",
                                show_statistics=False,
                                show_customization=False
                            )
                        else:
                            st.error(f"❌ {result.error_message}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        elif st.session_state.show_data_form == "control_chart":
            process_data = data_forms.process_data_form()
            if process_data:
                if st.button("Generate Control Chart", key="gen_control"):
                    try:
                        result = dynamic_tool_generator.generate_tool("control_chart", process_data)
                        if result.success:
                            st.success("✅ Control Chart Generated!")
                            tool_display.display_generated_tool(
                                {
                                    "success": True,
                                    "chart_data": result.chart_data,
                                    "statistics": result.data_summary
                                },
                                "control_chart",
                                show_statistics=False,
                                show_customization=False
                            )
                        else:
                            st.error(f"❌ {result.error_message}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        elif st.session_state.show_data_form == "histogram":
            process_data = data_forms.process_data_form()
            if process_data:
                if st.button("Generate Histogram", key="gen_histogram"):
                    try:
                        result = dynamic_tool_generator.generate_tool("histogram", process_data)
                        if result.success:
                            st.success("✅ Histogram Generated!")
                            tool_display.display_generated_tool(
                                {
                                    "success": True,
                                    "chart_data": result.chart_data,
                                    "statistics": result.data_summary
                                },
                                "histogram",
                                show_statistics=False,
                                show_customization=False
                            )
                        else:
                            st.error(f"❌ {result.error_message}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        elif st.session_state.show_data_form == "process_capability":
            process_data = data_forms.process_data_form()
            if process_data:
                if st.button("Generate Capability Analysis", key="gen_capability"):
                    try:
                        result = dynamic_tool_generator.generate_tool("process_capability", process_data)
                        if result.success:
                            st.success("✅ Process Capability Analysis Generated!")
                            tool_display.display_generated_tool(
                                {
                                    "success": True,
                                    "chart_data": result.chart_data,
                                    "statistics": result.data_summary
                                },
                                "process_capability",
                                show_statistics=False,
                                show_customization=False
                            )
                        else:
                            st.error(f"❌ {result.error_message}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Close form button
        if st.button("❌ Close Form", key="close_form"):
            st.session_state.show_data_form = None
            st.rerun()


# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tool_generated", False):
            # Show tool generation message
            st.markdown(msg["content"])
            
            # Display chart in collapsible section
            if msg.get("chart_data"):
                chart_title = f"📈 {msg['tool_type'].replace('_', ' ').title()}"
                with st.expander(chart_title, expanded=True):
                    tool_display.display_generated_tool(
                        {
                            "success": True,
                            "chart_data": msg["chart_data"],
                            "statistics": msg.get("data_summary", {})
                        },
                        msg["tool_type"],
                        show_statistics=False,
                        show_customization=False
                    )
                    
                    # Add export options
                    if msg.get("data_summary"):
                        export_manager.render_export_panel(
                            {
                                "success": True,
                                "chart_data": msg["chart_data"],
                                "statistics": msg.get("data_summary", {})
                            },
                            msg["tool_type"],
                            None,
                            msg.get("data_summary", {})
                        )
        else:
            st.markdown(msg["content"])

# Enhanced chat input with tool generation
if user_input := st.chat_input("Ask about QA tools, methods, SOPs, or generate charts..."):
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    

    # Get response with tool generation capability
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            custom_index = None
            if uploaded_file is not None:
                pdf_text = extract_text_from_pdf(uploaded_file)
                custom_index = build_temp_faiss(pdf_text, embeddings)

            image_payload = None
            if uploaded_image is not None and image_mode == "Ask about this image":
                image_payload = {
                    "bytes": uploaded_image.getvalue(),
                    "mime": uploaded_image.type or "image/jpeg"
                }
            csv_context = get_csv_excel_context()
            response = asyncio.run(
                ask_bot_with_escalation(
                    user_input,
                    chat_history=st.session_state.messages,
                    custom_index=custom_index,
                    image=image_payload,
                    mode="image" if image_payload else None,
                    recipient_email=st.session_state.get("recipient_email"),
                    persona=st.session_state.get("selected_persona", "Novice Guide"),
                    csv_context=csv_context
                )
            )

            # Handle different response types
            if response["type"] == "tool_generation":
                # Display generated tool
                st.success(response["message"])

                tool_result = response["tool_result"]
                tool_type = response["tool_type"]

                # Show the chart inline with collapsible functionality
                if tool_result.chart_data:
                    chart_title = f"📈 {tool_type.replace('_', ' ').title()}"
                    with st.expander(chart_title, expanded=True):
                        tool_display.display_generated_tool(
                            {
                                "success": True,
                                "chart_data": tool_result.chart_data,
                                "statistics": tool_result.data_summary
                            },
                            tool_type,
                            show_statistics=False,
                            show_customization=False
                        )

                        # Add export options
                        if tool_result.data_summary:
                            export_manager.render_export_panel(
                                {
                                    "success": True,
                                    "chart_data": tool_result.chart_data,
                                    "statistics": tool_result.data_summary
                                },
                                tool_type,
                                None,
                                tool_result.data_summary
                            )

                    # Store the response with chart data
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["message"],
                        "tool_generated": True,
                        "tool_type": tool_type,
                        "chart_data": tool_result.chart_data,
                        "data_summary": tool_result.data_summary
                    })

            elif response["type"] == "error":
                st.error(response["message"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["message"]
                })

            else:
                # Regular chat response
                st.markdown(response["message"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["message"]
                })

# Tool generation examples and help
if not st.session_state.messages:
    st.markdown("---")
    st.markdown("### 💡 Tool Generation Examples")

    # Create tabs for different examples
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Pareto Chart", "Fishbone Diagram", "Control Chart", "Histogram", "Process Capability"])

    with tab1:
        st.markdown("**Pareto Chart Examples:**")
        st.code("""
        Examples of what you can say:
        • "Generate a Pareto chart for these defects: Surface scratch 15, Dimensional error 8, Color mismatch 5, Packaging defect 3"
        • "Create a Pareto analysis for our quality issues: Crack 20, Warp 12, Bubble 6, Scratch 4"
        • "Build a Pareto chart showing defect frequencies: Type A 25, Type B 18, Type C 10, Type D 7"
        """)
        
        st.markdown("**What it does:**")
        st.info("Pareto charts help you identify the most significant problems by showing the frequency of different defect types, following the 80/20 rule.")

    with tab2:
        st.markdown("**Fishbone Diagram Examples:**")
        st.code("""
        Examples of what you can say:
        • "Create a fishbone diagram for our injection molding defects. Man: Training issues, Machine: Wear, Material: Contamination"
        • "Generate a root cause analysis for surface finish problems. Method: Incorrect parameters, Measurement: Calibration issues"
        • "Build a cause-effect diagram for dimensional variation. Environment: Temperature, Material: Batch variation"
        """)
        
        st.markdown("**What it does:**")
        st.info("Fishbone diagrams help you systematically analyze the root causes of problems using the 6M framework (Man, Machine, Material, Method, Measurement, Environment).")

    with tab3:
        st.markdown("**Control Chart Examples:**")
        st.code("""
        Examples of what you can say:
        • "Generate a control chart for these measurements: 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29, 1.30. USL: 1.35, LSL: 1.20"
        • "Create an X-bar chart for process data: 10.1, 10.2, 10.0, 10.3, 10.1, 10.2, 10.4, 10.0. Target: 10.2"
        • "Build a control chart for thickness measurements with specs 2.0-2.5mm"
        """)
        
        st.markdown("**What it does:**")
        st.info("Control charts help you monitor process variation over time and detect when a process goes out of control.")

    with tab4:
        st.markdown("**Histogram Examples:**")
        st.code("""
        Examples of what you can say:
        • "Generate a histogram for these measurements: 1.2, 1.3, 1.1, 1.4, 1.2, 1.3, 1.1, 1.4, 1.2, 1.3"
        • "Create a distribution analysis for process output data with USL: 10.5, LSL: 9.5"
        • "Build a histogram showing the spread of our quality measurements"
        """)
        
        st.markdown("**What it does:**")
        st.info("Histograms help you understand the distribution and spread of your measurement data, including whether it follows a normal distribution.")

    with tab5:
        st.markdown("**Process Capability Examples:**")
        st.code("""
        Examples of what you can say:
        • "Generate a process capability analysis for measurements: 1.23, 1.24, 1.25, 1.26, 1.27. USL: 1.30, LSL: 1.20, Target: 1.25"
        • "Create a Cp/Cpk analysis for our manufacturing process with specification limits 10.0-10.5"
        • "Build a capability study for dimensional measurements with target 5.0mm, tolerance ±0.1mm"
        """)
        
        st.markdown("**What it does:**")
        st.info("Process capability analysis evaluates how well your process meets specification limits and calculates Cp, Cpk, and sigma levels.")

    # Add help section
    st.markdown("---")
    st.markdown("### ❓ Need Help?")
    st.info("""
    **Quick Tips:**
    - Use natural language to describe your data and what you want to analyze
    - Be specific about defect types, measurement values, and specification limits
    - The AI will automatically extract the relevant information from your description
    - You can also use the manual data entry forms in the sidebar for more control
    - All generated tools can be customized and exported in multiple formats
    """)

