import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os
#from dotenv import load_dotenv
from tool_recommender import check_for_tool, check_for_tool_generation, enhanced_tool_lookup
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import re
# Add these imports
from dynamic_tool_generator import DynamicToolGenerator
from ai_data_parser import AIDataParser
from ui_components import ToolDisplayComponent, DataInputForms, ToolCustomizationPanel, ExportManager
from email_config import EmailEscalation

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Load environment variables
#load_dotenv()
#genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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


async def ask_bot(query, chat_history=None, custom_index=None, image=None, mode=None):
    # Vision-only path: if an image is provided and mode is image, analyze image directly
    if mode == "image" and image is not None:
        loop = asyncio.get_event_loop()
        tool_future = loop.run_in_executor(executor, get_tool_recommendation, query)

        prompt_text = (
            "You are a quality assurance assistant. Analyze the provided image in the context of the user's question. "
            "Use a friendly, conversational tone. Ask a brief clarifying question when ambiguity would change the answer. "
            "Describe observations succinctly, infer relevant QA implications (e.g., control charts, defects, measurement setups), "
            "and recommend a quality tool if helpful. Be concise and well-organized. "
            "Only say you don't know if the request is outside the QA scope, requires unavailable data from the image, or is a technical limitation."
        )

        # Gemini expects inline image data as bytes with mime type
        response = model.generate_content([
            {"text": prompt_text + "\n\nQuestion: " + query},
            {"inline_data": {"mime_type": image.get("mime", "image/jpeg"), "data": image.get("bytes", b"")}},
        ])
        tool_recommendation = await tool_future
        return (response.text or "") .strip() + tool_recommendation

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

    # Format memory (last 15 exchanges)
    memory_context = ""
    if chat_history:
        for msg in chat_history[-30:]:  # Last 5 rounds
            role = "User" if msg["role"] == "user" else "Assistant"
            memory_context += f"{role}: {msg['content']}\n"

    # Final prompt
    prompt = f"""
You are a quality assurance assistant. Use the provided SOP context, uploaded PDFs, and recent conversation to answer the user’s latest question.

Rules:

1. Answer generic QA questions using the SOP context.

2. Only answer client-specific questions if relevant PDFs are provided. If no PDFs or relevant content exist, reply: “I can’t answer this without the relevant documents. Please upload the PDFs so I can help.”

3. Be conversational, concise, and helpful.

4. Ask a brief clarifying question if the request is ambiguous.

5. Include citations [n] only when referencing documents.

6. Recommend one or more quality tools from the following list only: Pareto chart, Histogram, Control chart, Capability chart, Fishbone diagram. Do not suggest any tools outside of this list.

7. Do not make assumptions outside the QA scope or provided documents.

8. If asked to make a decision, suggest the quality tools to use and then ask the user to make the decision.

9. If asked to use a tool outside of Pareto chart, Histogram, Control chart, Capability chart, or Fishbone diagram, reply that you cannot do so and politely ask if you can help in another way.

10. If provided with data, recommend the suitable quality tools at the end of your response and then ask the user to make the decision.

Recent Conversation:
{memory_context}

Document Context:
{doc_context}

Current Question:
{query}

Your response should:

1. Directly address the question within scope.

2. Reference sources using [n] only when citing documents.

3. Recommend quality tools where applicable.

4. Be concise, conversational, and organized.
"""

    # Wait for tool recommendation to finish
    tool_recommendation = await tool_future

    # Generate answer from Gemini
    response = model.generate_content(prompt)
    answer = response.text.strip() + tool_recommendation

    # Add citation list only if citations are present in the answer
    if source_map:
        used_ids = [sid for sid in source_map.keys() if sid in answer]
        if used_ids:
            sources_section = "\n\nSources:"
            for source_id in used_ids:
                source = source_map[source_id]
                if isinstance(source, str):
                    sources_section += f"\n{source_id} {os.path.basename(source)}"
                else:
                    sources_section += f"\n{source_id} Uploaded Document"
            answer += sources_section

    return answer


# Initialize global resources for tool generation
dynamic_tool_generator = DynamicToolGenerator()
ai_data_parser = AIDataParser()
tool_display = ToolDisplayComponent()
data_forms = DataInputForms()
tool_customization = ToolCustomizationPanel()
export_manager = ExportManager()

async def generate_qc_tool(query: str, chat_history=None, custom_index=None, image=None, mode=None):
    """Generate actual QC tools based on user input"""

    # Always scan recent user messages for numeric data
    search_query = query
    if chat_history:
        found_numeric = False
        for msg in reversed(chat_history[-5:]):  # Look back at last 5 user messages
            if msg["role"] == "user":
                # Check if the message contains at least 2 numbers (to be considered "data")
                import re
                numbers = re.findall(r'(\d+\.?\d*)', msg["content"])
                if len(numbers) >= 2:
                    search_query = msg["content"]
                    found_numeric = True
                    break
        # If no numeric history found, just stick with current query
        if not found_numeric:
            search_query = query

    query_lower = search_query.lower()

    # PARETO CHART
    if "pareto" in query_lower:
        import re
        # Look for patterns like "Surface scratch 15, Dimensional error 8"
        defect_pattern = r'([^,]+?)\s+(\d+)'
        matches = re.findall(defect_pattern, search_query)

        if matches:
            categories = []
            counts = []

            for category, count in matches:
                categories.append(category.strip())
                counts.append(int(count))

            from data_extractor import DefectData
            total_defects = sum(counts)
            frequencies = [count / total_defects for count in counts]

            defect_data = DefectData(
                categories=categories,
                counts=counts,
                frequencies=frequencies,
                total_defects=total_defects,
                source="ai_extraction"
            )

            try:
                result = dynamic_tool_generator.generate_tool("pareto_chart", defect_data)
                return result, None
            except Exception as e:
                return None, f"Error generating Pareto chart: {str(e)}"

    # CONTROL CHART
    elif "control chart" in query_lower or ("control" in query_lower and "chart" in query_lower):
        import re
        from data_extractor import ProcessData

        measurement_pattern = r'(\d+\.?\d*)'
        measurements = [float(m) for m in re.findall(measurement_pattern, search_query) if float(m) > 0]

        usl_pattern = r'usl[:\s]*(\d+\.?\d*)'
        lsl_pattern = r'lsl[:\s]*(\d+\.?\d*)'
        target_pattern = r'target[:\s]*(\d+\.?\d*)'

        usl_match = re.search(usl_pattern, search_query)
        lsl_match = re.search(lsl_pattern, search_query)
        target_match = re.search(target_pattern, search_query)

        specifications = {}
        if usl_match:
            specifications['usl'] = float(usl_match.group(1))
        if lsl_match:
            specifications['lsl'] = float(lsl_match.group(1))
        if target_match:
            specifications['target'] = float(target_match.group(1))

        if measurements:
            process_data = ProcessData(
                measurements=measurements,
                specifications=specifications,
                sample_size=len(measurements)
            )

            try:
                result = dynamic_tool_generator.generate_tool("control_chart", process_data)
                return result, None
            except Exception as e:
                return None, f"Error generating Control chart: {str(e)}"

    # HISTOGRAM
    elif "histogram" in query_lower:
        import re
        from data_extractor import ProcessData

        measurement_pattern = r'(\d+\.?\d*)'
        measurements = [float(m) for m in re.findall(measurement_pattern, search_query) if float(m) > 0]

        usl_pattern = r'usl[:\s]*(\d+\.?\d*)'
        lsl_pattern = r'lsl[:\s]*(\d+\.?\d*)'
        target_pattern = r'target[:\s]*(\d+\.?\d*)'

        usl_match = re.search(usl_pattern, search_query)
        lsl_match = re.search(lsl_pattern, search_query)
        target_match = re.search(target_pattern, search_query)

        specifications = {}
        if usl_match:
            specifications['usl'] = float(usl_match.group(1))
        if lsl_match:
            specifications['lsl'] = float(lsl_match.group(1))
        if target_match:
            specifications['target'] = float(target_match.group(1))

        if measurements:
            process_data = ProcessData(
                measurements=measurements,
                specifications=specifications,
                sample_size=len(measurements)
            )

            try:
                result = dynamic_tool_generator.generate_tool("histogram", process_data)
                return result, None
            except Exception as e:
                return None, f"Error generating Histogram: {str(e)}"
    # PROCESS CAPABILITY
    elif "capability" in query_lower or "cp" in query_lower or "cpk" in query_lower or "cp/cpk" in query_lower:
        import re
        from data_extractor import ProcessData
        
        # Extract measurements
        measurement_pattern = r'(\d+\.?\d*)'
        measurements = [float(m) for m in re.findall(measurement_pattern, search_query) if float(m) > 0]
        
        # Extract specification limits - improved patterns
        usl_pattern = r'usl[:\s]*(\d+\.?\d*)'
        lsl_pattern = r'lsl[:\s]*(\d+\.?\d*)'
        target_pattern = r'target[:\s]*(\d+\.?\d*)'
        
        # Add range pattern for "10.0-10.5" format
        range_pattern = r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)'
        range_match = re.search(range_pattern, search_query)
        
        usl_match = re.search(usl_pattern, search_query)
        lsl_match = re.search(lsl_pattern, search_query)
        target_match = re.search(target_pattern, search_query)
        
        specifications = {}
        
        # Handle range specifications like "10.0-10.5"
        if range_match:
            specifications['lsl'] = float(range_match.group(1))
            specifications['usl'] = float(range_match.group(2))
            specifications['target'] = (float(range_match.group(1)) + float(range_match.group(2))) / 2
        else:
            if usl_match:
                specifications['usl'] = float(usl_match.group(1))
            if lsl_match:
                specifications['lsl'] = float(lsl_match.group(1))
            if target_match:
                specifications['target'] = float(target_match.group(1))
        
        # Generate sample data if no measurements provided but specifications exist
        if not measurements and specifications:
            # Generate sample measurements within the specification range
            if 'lsl' in specifications and 'usl' in specifications:
                lsl = specifications['lsl']
                usl = specifications['usl']
                target = specifications.get('target', (lsl + usl) / 2)
                # Generate 30 sample points normally distributed around target
                import numpy as np
                std_dev = (usl - lsl) / 6  # Assume 6-sigma process
                measurements = np.random.normal(target, std_dev, 30).tolist()
                measurements = [max(lsl, min(usl, m)) for m in measurements]  # Clamp to spec limits
        
        if measurements and specifications:
            process_data = ProcessData(
                measurements=measurements,
                specifications=specifications,
                sample_size=len(measurements)
            )
            
            try:
                result = dynamic_tool_generator.generate_tool("capability_chart", process_data)
                return result, None
            except Exception as e:
                return None, f"Error generating Process Capability analysis: {str(e)}"
        elif specifications and not measurements:
            return None, "I can create a capability analysis, but I need actual measurement data. Please provide the measurements you want to analyze."
        else:
            return None, "I need specification limits (like USL/LSL or a range like 10.0-10.5) to create a capability analysis."
    
    # FISHBONE DIAGRAM
    elif "fishbone" in query_lower or "root cause" in query_lower or ("cause" in query_lower and "diagram" in query_lower):
        from data_extractor import CauseEffectData
        import re
        
        # Extract problem statement
        problem = "Quality problem"  # Default
        if "defect" in query_lower:
            problem = "Defect analysis"
        elif "problem" in query_lower:
            problem = "Problem analysis"
        
        # Extract cause categories and sub-causes
        main_categories = []
        sub_causes = {}
        
        # Look for 6M framework
        categories = ['man', 'machine', 'material', 'method', 'measurement', 'environment']
        
        for category in categories:
            # Look for patterns like "Man: Training issues, Machine: Wear"
            pattern = f'{category}[:\s]*([^,]+)'
            matches = re.findall(pattern, query_lower)
            if matches:
                main_categories.append(category.title())
                sub_causes[category.title()] = [match.strip() for match in matches]
        
        if main_categories:
            cause_data = CauseEffectData(
                problem=problem,
                main_categories=main_categories,
                sub_causes=sub_causes,
                confidence=0.8
            )
            
            try:
                result = dynamic_tool_generator.generate_tool("fishbone_diagram", cause_data)
                return result, None
            except Exception as e:
                return None, f"Error generating Fishbone diagram: {str(e)}"
    
    return None, "No tool generation requested"
    
def get_tool_generation_suggestion(query: str) -> str:
    """Get suggestion for tool generation based on query"""
    
    tool_match = check_for_tool_generation(query)
    
    if not tool_match["match"]:
        return ""
    
    if tool_match["should_generate"]:
        return f"\n\n🎯 **I can generate a {tool_match['tool']} for you!**\nI found sufficient data in your message to create this tool automatically.\n\nType 'Generate {tool_match['tool']}' to create it, or ask me to help you with the data if needed."
    
    elif tool_match["can_generate"] and not tool_match["data_sufficient"]:
        missing_data = tool_match["required_data"].replace("_", " ").title()
        min_points = tool_match["min_data_points"]
        return f"\n\n�� **I can generate a {tool_match['tool']} for you!**\nHowever, I need more {missing_data} to create it. I need at least {min_points} data points.\n\nPlease provide more specific data, or ask me to help you structure the information."
    
    else:
        # Fall back to regular recommendation
        confidence = tool_match.get("confidence", 0) * 100
        return f"\n\nRecommended Quality Tool: **{tool_match['tool']}** (Confidence: {confidence:.1f}%)\n{tool_match['when_to_use']}"

def get_chart_explanation(tool_type: str, data_summary: dict = None) -> str:
    """Generate explanation for the generated chart"""
    
    explanations = {
        "histogram": """
**📊 Histogram Analysis:**
This histogram shows the distribution of your measurements. It helps you understand:
- **Shape**: Whether your data is normally distributed, skewed, or has multiple peaks
- **Center**: Where most of your measurements cluster
- **Spread**: How much variation exists in your process
- **Specification Limits**: How your data relates to USL/LSL boundaries

**Key Insights to Look For:**
- Data should cluster around the target value
- Most points should fall within specification limits
- The shape should be roughly bell-shaped for a stable process
        """,
        
        "control_chart": """
**📈 Control Chart Analysis:**
This control chart monitors your process stability over time. It shows:
- **Center Line**: The average of your measurements
- **Control Limits**: Upper and Lower Control Limits (UCL/LCL) based on process variation
- **Specification Limits**: Your USL/LSL requirements
- **Data Points**: Individual measurements plotted in sequence

**Key Insights to Look For:**
- Points should stay within control limits
- No patterns or trends (runs, cycles, or systematic changes)
- Points should be randomly distributed around the center line
- Any points outside control limits indicate special causes
        """,
        
        "pareto_chart": """
**�� Pareto Chart Analysis:**
This Pareto chart follows the 80/20 rule to prioritize problems. It shows:
- **Defect Categories**: Different types of problems ranked by frequency
- **Cumulative Percentage**: Running total showing which categories contribute most
- **80/20 Line**: Helps identify the vital few categories causing most issues

**Key Insights to Look For:**
- Focus on the top 2-3 categories (they likely cause 80% of problems)
- Categories to the right of the 80% line are the "trivial many"
- Prioritize improvement efforts on the highest-impact categories
        """,
        
        "capability_chart": """
**�� Process Capability Analysis:**
This chart evaluates how well your process meets specifications. It shows:
- **Process Distribution**: How your measurements are spread
- **Specification Limits**: Your USL/LSL requirements
- **Capability Indices**: Cp and Cpk values indicating process performance
- **Target**: Your ideal process center

**Key Insights to Look For:**
- **Cp ≥ 1.33**: Process spread is acceptable
- **Cpk ≥ 1.33**: Process is centered and capable
- **Cpk < 1.0**: Process needs improvement
- Data should be centered on target with minimal variation
        """,
        
        "fishbone_diagram": """
**🐟 Fishbone Diagram Analysis:**
This cause-and-effect diagram helps identify potential root causes. It organizes causes into:
- **Man**: Human factors (training, skill, fatigue)
- **Machine**: Equipment issues (wear, maintenance, calibration)
- **Material**: Input variations (supplier, quality, specifications)
- **Method**: Process procedures (work instructions, standards)
- **Measurement**: Data collection issues (accuracy, precision)
- **Environment**: External factors (temperature, humidity, lighting)

**Key Insights to Look For:**
- Focus on the most likely causes in each category
- Look for interactions between different cause categories
- Prioritize causes that are easiest to control or measure
        """
    }
    
    base_explanation = explanations.get(tool_type, f"**📊 {tool_type.replace('_', ' ').title()} Analysis:**\nThis chart helps analyze your quality data.")
    
    # Add specific insights based on data if available
    if data_summary and tool_type in ["histogram", "control_chart", "capability_chart"]:
        if "mean" in data_summary:
            base_explanation += f"\n\n**Your Data Summary:**\n- Mean: {data_summary.get('mean', 'N/A'):.3f}"
        if "std_dev" in data_summary:
            base_explanation += f"\n- Standard Deviation: {data_summary.get('std_dev', 'N/A'):.3f}"
        if "sample_size" in data_summary:
            base_explanation += f"\n- Sample Size: {data_summary.get('sample_size', 'N/A')}"
    
    return base_explanation
async def ask_bot_with_tool_generation(query, chat_history=None, custom_index=None, image=None, mode=None):
    """Enhanced ask_bot function with tool generation capability"""
    
    # Check if this is a tool generation request
    if any(keyword in query.lower() for keyword in ["generate", "create", "build", "make", "pareto", "histogram", "control chart", "capability", "fishbone", "chart"]):
        tool_result, error = await generate_qc_tool(query, chat_history, custom_index, image, mode)
        
        if tool_result and tool_result.success:
            # Generate chart explanation
            explanation = get_chart_explanation(tool_result.tool_type, tool_result.data_summary)
            
            return {
                "type": "tool_generation",
                "tool_result": tool_result,
                "tool_type": tool_result.tool_type,
                "message": f"✅ Successfully generated {tool_result.tool_type.replace('_', ' ').title()}\n\n{explanation}"
            }
        elif error:
            return {
                "type": "error",
                "message": f"❌ {error}"
            }
    
    # Fall back to regular chatbot response
    regular_response = await ask_bot(query, chat_history, custom_index, image, mode)
    
    # Add tool generation suggestion
    suggestion = get_tool_generation_suggestion(query)
    
    return {
        "type": "chat_response",
        "message": regular_response + suggestion
    }

async def ask_bot_with_escalation(query, chat_history=None, custom_index=None, image=None, mode=None, recipient_email=None):
    """Enhanced ask_bot function with LLM-determined escalation"""
    
    # Get the original response
    response = await ask_bot_with_tool_generation(query, chat_history, custom_index, image, mode)
    
    # Extract response text
    if response["type"] == "chat_response":
        response_text = response["message"]
    elif response["type"] == "tool_generation":
        response_text = response["message"]
    elif response["type"] == "error":
        response_text = response["message"]
    else:
        response_text = response.get("message", "")
    
    # Ask the LLM to assess its own confidence and determine if escalation is needed
    confidence_check_prompt = f"""
Based on your previous response to the user's question, please assess your confidence level and determine if human escalation is needed.

User's Question: {query}
Your Response: {response_text}

Please respond with ONLY one of these options:
1. "ESCALATE" - if you are uncertain, lack sufficient information, or need human expertise
2. "CONFIDENT" - if you are confident in your response and no escalation is needed

Do not provide any explanation, just respond with either "ESCALATE" or "CONFIDENT".
"""
    
    # Get LLM's self-assessment
    confidence_response = model.generate_content(confidence_check_prompt)
    confidence_decision = confidence_response.text.strip().upper()
    
    # Check if escalation is needed
    if "ESCALATE" in confidence_decision:
        # Send escalation email
        email_escalation = EmailEscalation()
        escalation_sent = email_escalation.send_escalation_email(
            query, response_text, "LLM determined uncertainty", recipient_email
        )
        
        # Add escalation notice to response
        email_used = recipient_email or "default manager"
        escalation_notice = f"""
        
⚠️ **Human Escalation Required**

I've determined that your query requires human expertise beyond my capabilities. I've escalated your question to our quality experts who will review it and get back to you.

**Escalation Status:** {'✅ Sent' if escalation_sent else '❌ Failed to send'}
**Escalated to:** {email_used}
        """
        
        if response["type"] == "chat_response":
            response["message"] += escalation_notice
        elif response["type"] == "tool_generation":
            response["message"] += escalation_notice
        elif response["type"] == "error":
            response["message"] += escalation_notice
        
        # Add escalation info to response
        response["escalated"] = True
        response["escalation_sent"] = escalation_sent
    
    return response