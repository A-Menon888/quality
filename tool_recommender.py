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
