#!/usr/bin/env python3
"""
Debug script to test chart detection logic
"""

def test_detection_logic():
    """Test the detection logic with various inputs"""
    
    print("=== TESTING CHART DETECTION LOGIC ===")
    
    test_queries = [
        "a histogram please",
        "yes, create a pareto chart", 
        "histogram",
        "pareto chart",
        "yes, a histogram",
        "create histogram",
        "generate pareto chart"
    ]
    
    for query in test_queries:
        query_lower = query.lower()
        
        # Test the detection logic
        is_tool_request = (
            any(keyword in query_lower for keyword in ["generate", "create", "build", "make", "chart"]) or
            any(tool in query_lower for tool in ["pareto", "histogram", "control chart", "capability", "fishbone"]) or
            ("yes" in query_lower and any(tool in query_lower for tool in ["histogram", "pareto", "control", "capability", "fishbone"])) or
            ("please" in query_lower and any(tool in query_lower for tool in ["histogram", "pareto", "control", "capability", "fishbone"])) or
            ("a " in query_lower and any(tool in query_lower for tool in ["histogram", "pareto", "control", "capability", "fishbone"]))
        )
        
        print(f"Query: '{query}'")
        print(f"  Lower: '{query_lower}'")
        print(f"  Detected: {is_tool_request}")
        print()

if __name__ == "__main__":
    test_detection_logic()
