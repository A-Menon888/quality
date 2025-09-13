from sentence_transformers import SentenceTransformer
import numpy as np

# Enhanced tool descriptions with more context and examples
tool_lookup = {
    "pareto_chart": {
        "tool": "Pareto Chart",
        "when_to_use": "Use when you want to prioritize issues based on how often they occur.",
        "descriptions": [
            "analyze frequency of defects",
            "identify most common problems",
            "prioritize quality issues",
            "find frequent failures",
            "count occurrence of problems"
        ]
    },
    "root_cause": {
        "tool": "5-Why or Fishbone Diagram",
        "when_to_use": "Use when you need to analyze the underlying cause of a problem.",
        "descriptions": [
            "find root cause of issue",
            "analyze why problem occurs",
            "determine cause and effect",
            "investigate problem source",
            "diagnose underlying issues"
        ]
    },
    "process_capability": {
        "tool": "Cp/Cpk Analysis",
        "when_to_use": "Use when evaluating how well a process meets specification limits.",
        "descriptions": [
            "measure process capability",
            "check specification limits",
            "analyze process performance",
            "evaluate manufacturing capability",
            "assess process variation"
        ]
    },
    "control_chart": {
        "tool": "Control Chart",
        "when_to_use": "Use to monitor process variation over time.",
        "descriptions": [
            "track process variation",
            "monitor quality metrics",
            "analyze trends over time",
            "detect process shifts",
            "identify out of control conditions"
        ]
    },
    "histogram": {
        "tool": "Histogram",
        "when_to_use": "Use to understand the distribution and spread of measurement data.",
        "descriptions": [
            "analyze data distribution",
            "check measurement spread",
            "visualize process output",
            "examine data patterns",
            "assess normal distribution"
        ]
    }
}

# Initialize the sentence transformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def check_for_tool(query: str, threshold=0.6):
    """
    Check if a query matches any quality tool using semantic similarity.
    
    Args:
        query (str): The user's question or request
        threshold (float): Minimum similarity score to consider a match (0-1)
        
    Returns:
        dict: Tool match information or no match
    """
    # Encode the query
    query_embedding = model.encode(query.lower())
    
    best_match = {"match": False}
    highest_score = 0
    
    # Check each tool and its descriptions
    for tool_id, info in tool_lookup.items():
        # Encode all descriptions for this tool
        tool_descriptions = info["descriptions"]
        description_embeddings = model.encode(tool_descriptions)
        
        # Calculate similarities with all descriptions
        similarities = np.dot(description_embeddings, query_embedding)
        max_similarity = np.max(similarities)
        
        # Update if this is the best match so far
        if max_similarity > highest_score and max_similarity >= threshold:
            highest_score = max_similarity
            best_match = {
                "match": True,
                "tool": info["tool"],
                "when_to_use": info["when_to_use"],
                "confidence": float(max_similarity)
            }
    
    return best_match

# Add these imports at the top of the file (after line 2)
from data_extractor import DataExtractor, DefectData, ProcessData, CauseEffectData

# Add this enhanced tool lookup with generation capabilities
enhanced_tool_lookup = {
    "pareto_chart": {
        "tool": "Pareto Chart",
        "when_to_use": "Use when you want to prioritize issues based on how often they occur.",
        "can_generate": True,
        "required_data": "defect_data",
        "min_data_points": 3,
        "descriptions": [
            "analyze frequency of defects",
            "identify most common problems", 
            "prioritize quality issues",
            "find frequent failures",
            "count occurrence of problems",
            "generate pareto chart",
            "create pareto analysis",
            "build pareto diagram"
        ]
    },
    "fishbone_diagram": {
        "tool": "Fishbone Diagram",
        "when_to_use": "Use when you need to analyze the underlying causes of a problem.",
        "can_generate": True,
        "required_data": "cause_effect_data",
        "min_data_points": 2,
        "descriptions": [
            "find root cause of issue",
            "analyze why problem occurs",
            "determine cause and effect",
            "investigate problem source",
            "diagnose underlying issues",
            "create fishbone diagram",
            "build cause and effect diagram",
            "generate ishikawa diagram"
        ]
    },
    "control_chart": {
        "tool": "Control Chart",
        "when_to_use": "Use to monitor process variation over time.",
        "can_generate": True,
        "required_data": "process_data",
        "min_data_points": 20,
        "descriptions": [
            "track process variation",
            "monitor quality metrics",
            "analyze trends over time",
            "detect process shifts",
            "identify out of control conditions",
            "generate control chart",
            "create control chart",
            "build control chart"
        ]
    },
    "histogram": {
        "tool": "Histogram",
        "when_to_use": "Use to understand the distribution and spread of measurement data.",
        "can_generate": True,
        "required_data": "process_data",
        "min_data_points": 10,
        "descriptions": [
            "analyze data distribution",
            "check measurement spread",
            "visualize process output",
            "examine data patterns",
            "assess normal distribution",
            "generate histogram",
            "create histogram",
            "build histogram"
        ]
    },
    "process_capability": {
        "tool": "Process Capability Analysis",
        "when_to_use": "Use when evaluating how well a process meets specification limits.",
        "can_generate": True,
        "required_data": "process_data",
        "min_data_points": 30,
        "descriptions": [
            "measure process capability",
            "check specification limits",
            "analyze process performance",
            "evaluate manufacturing capability",
            "assess process variation",
            "generate capability analysis",
            "create cp cpk chart",
            "build process capability chart"
        ]
    }
}

def check_for_tool_generation(query: str, threshold=0.6):
    """
    Enhanced tool detection that determines if we should generate or just recommend a tool.
    
    Args:
        query (str): The user's question or request
        threshold (float): Minimum similarity score to consider a match (0-1)
        
    Returns:
        dict: Tool match information with generation capability
    """
    # Initialize data extractor
    extractor = DataExtractor()
    
    # Encode the query
    query_embedding = model.encode(query.lower())
    
    best_match = {"match": False, "should_generate": False}
    highest_score = 0
    
    # Check each tool and its descriptions
    for tool_id, info in enhanced_tool_lookup.items():
        # Encode all descriptions for this tool
        tool_descriptions = info["descriptions"]
        description_embeddings = model.encode(tool_descriptions)
        
        # Calculate similarities with all descriptions
        similarities = np.dot(description_embeddings, query_embedding)
        max_similarity = np.max(similarities)
        
        # Update if this is the best match so far
        if max_similarity > highest_score and max_similarity >= threshold:
            highest_score = max_similarity
            
            # Check if we can generate this tool
            can_generate = info.get("can_generate", False)
            required_data = info.get("required_data", None)
            min_data_points = info.get("min_data_points", 0)
            
            # Try to extract required data
            data_sufficient = False
            extracted_data = None
            
            if required_data == "defect_data":
                extracted_data = extractor.extract_defect_data(query)
                data_sufficient = extracted_data and len(extracted_data.categories) >= min_data_points
            elif required_data == "process_data":
                extracted_data = extractor.extract_process_data(query)
                data_sufficient = extracted_data and len(extracted_data.measurements) >= min_data_points
            elif required_data == "cause_effect_data":
                extracted_data = extractor.extract_cause_effect_data(query)
                data_sufficient = extracted_data and len(extracted_data.main_categories) >= min_data_points
            
            should_generate = can_generate and data_sufficient
            
            best_match = {
                "match": True,
                "tool": info["tool"],
                "when_to_use": info["when_to_use"],
                "confidence": float(max_similarity),
                "should_generate": should_generate,
                "can_generate": can_generate,
                "required_data": required_data,
                "extracted_data": extracted_data,
                "data_sufficient": data_sufficient,
                "min_data_points": min_data_points
            }
    
    return best_match

def get_generation_suggestion(query: str, tool_match: dict) -> str:
    """
    Generate a suggestion for tool generation based on the match and data availability.
    
    Args:
        query (str): Original user query
        tool_match (dict): Result from check_for_tool_generation
        
    Returns:
        str: Suggestion message for the user
    """
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