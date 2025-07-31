tool_lookup = {
    "defect frequency": {
        "tool": "Pareto Chart",
        "when_to_use": "Use when you want to prioritize issues based on how often they occur."
    },
    "root cause": {
        "tool": "5-Why or Fishbone Diagram",
        "when_to_use": "Use when you need to analyze the underlying cause of a problem."
    },
    "process capability": {
        "tool": "Cp/Cpk Analysis",
        "when_to_use": "Use when evaluating how well a process meets specification limits."
    },
    "variation": {
        "tool": "Control Chart",
        "when_to_use": "Use to monitor process variation over time."
    }
}

def check_for_tool(query: str):
    query_lower = query.lower()
    for keyword, info in tool_lookup.items():
        if keyword in query_lower:
            return {
                "match": True,
                "keyword": keyword,
                "tool": info["tool"],
                "when_to_use": info["when_to_use"]
            }
    return {"match": False}
