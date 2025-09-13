# AI-Powered Data Extraction Implementation

## Overview

The Quality Assurance chatbot now uses **Gemini AI as the primary mechanism** for extracting structured data from conversation history, with regex pattern matching as a fallback. This enhancement significantly improves the system's ability to understand context and extract relevant data from natural language conversations.

## Key Features

### 1. **Primary AI Extraction**
- Uses Google Gemini to analyze the last 5 conversations
- Extracts structured data in the exact format required by chart generators
- Understands context and relationships between data points
- Handles complex, natural language descriptions of data

### 2. **Intelligent Fallback**
- Falls back to regex extraction if AI fails
- Maintains backward compatibility with existing patterns
- Ensures system reliability even when AI is unavailable

### 3. **Enhanced Data Understanding**
- Recognizes data across multiple conversation turns
- Understands implicit relationships and context
- Extracts specifications, measurements, and categories intelligently

## Implementation Details

### Core Function: `generate_qc_tool()`

```python
async def generate_qc_tool(query: str, chat_history=None, custom_index=None, image=None, mode=None):
    """Generate actual QC tools based on user input"""

    # Primary mechanism: Use AI to extract data from conversation history
    search_query = query
    extracted_data = None
    
    if chat_history:
        # Prepare conversation context for AI analysis
        conversation_context = ""
        for msg in chat_history[-5:]:  # Last 5 conversations
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n"
        
        # Use AI to extract structured data from conversation history
        try:
            extracted_data = ai_data_parser.extract_structured_data(query, conversation_context)
            
            # If AI found relevant data, use it for chart generation
            if extracted_data and any(extracted_data.values()):
                search_query = query  # Keep original query for tool type detection
                # The extracted_data will be used directly in chart generation
            else:
                # Fallback to regex-based extraction
                search_query = await _fallback_regex_extraction(query, chat_history)
        except Exception as e:
            print(f"AI data extraction failed: {e}")
            # Fallback to regex-based extraction
            search_query = await _fallback_regex_extraction(query, chat_history)
    else:
        search_query = query
```

### AI Data Extraction Process

1. **Conversation Context Preparation**: Last 5 conversations are formatted for AI analysis
2. **AI Analysis**: Gemini analyzes the context and extracts structured data
3. **Data Validation**: Checks if AI found relevant data
4. **Chart Generation**: Uses AI-extracted data for chart creation
5. **Fallback**: Falls back to regex if AI fails

### Chart-Specific AI Extraction

#### **Pareto Chart**
```python
# Try AI-extracted data first
if extracted_data and extracted_data.get('defect_data'):
    defect_info = extracted_data['defect_data']
    if defect_info.get('categories') and defect_info.get('counts'):
        # Use AI-extracted defect data
        categories = defect_info['categories']
        counts = defect_info['counts']
        # ... create DefectData object
```

#### **Control Chart & Histogram**
```python
# Try AI-extracted data first
if extracted_data and extracted_data.get('process_data'):
    process_info = extracted_data['process_data']
    if process_info.get('measurements'):
        # Use AI-extracted process data
        measurements = process_info['measurements']
        specifications = process_info.get('specifications', {})
        # ... create ProcessData object
```

#### **Process Capability**
```python
# Try AI-extracted data first
if extracted_data and extracted_data.get('process_data'):
    process_info = extracted_data['process_data']
    if process_info.get('measurements') and process_info.get('specifications'):
        # Use AI-extracted data with specifications
        measurements = process_info['measurements']
        specifications = process_info['specifications']
        # ... create ProcessData object
```

#### **Fishbone Diagram**
```python
# Try AI-extracted data first
if extracted_data and extracted_data.get('cause_effect_data'):
    cause_info = extracted_data['cause_effect_data']
    if cause_info.get('main_categories') and cause_info.get('sub_causes'):
        # Use AI-extracted cause-effect data
        cause_data = CauseEffectData(
            problem=cause_info.get('problem', 'Quality problem'),
            main_categories=cause_info['main_categories'],
            sub_causes=cause_info['sub_causes'],
            confidence=0.9  # Higher confidence for AI extraction
        )
```

### Fallback Mechanism

```python
async def _fallback_regex_extraction(query: str, chat_history=None):
    """Fallback mechanism using regex to extract data from conversation history"""
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
    return search_query
```

## Usage Examples

### Example 1: Pareto Chart with AI Extraction

**Conversation History:**
```
User: I need help with quality analysis
Assistant: I can help you with quality analysis. What specific data do you have?
User: We have some defect data from our production line
Assistant: Great! What types of defects are you seeing?
User: Surface scratches: 45 cases, Dimensional errors: 32 cases, Color mismatches: 28 cases, Packaging defects: 15 cases, Other issues: 8 cases
Assistant: That's a good dataset. What would you like to analyze?
User: Generate a Pareto chart
```

**AI Extraction Result:**
```json
{
  "defect_data": {
    "categories": ["Surface scratches", "Dimensional errors", "Color mismatches", "Packaging defects", "Other issues"],
    "counts": [45, 32, 28, 15, 8],
    "time_period": null
  }
}
```

### Example 2: Histogram with AI Extraction

**Conversation History:**
```
User: I need to analyze some measurement data
Assistant: I can help with measurement analysis. What data do you have?
User: We measured 50 parts from our CNC machining process
Assistant: What are the measurements and specifications?
User: Measurements: 10.2, 10.1, 10.3, 10.0, 10.4... USL: 10.5, LSL: 9.5, Target: 10.0
Assistant: That's a comprehensive dataset. What analysis would you like?
User: Create a histogram
```

**AI Extraction Result:**
```json
{
  "process_data": {
    "measurements": [10.2, 10.1, 10.3, 10.0, 10.4, ...],
    "specifications": {
      "usl": 10.5,
      "lsl": 9.5,
      "target": 10.0
    },
    "process_name": "CNC machining"
  }
}
```

### Example 3: Fishbone Diagram with AI Extraction

**Conversation History:**
```
User: We're having quality issues with our product
Assistant: I can help with root cause analysis. What specific problems are you seeing?
User: We're getting surface defects on our machined parts
Assistant: Let's analyze the potential causes. What factors might be involved?
User: Man: Operator fatigue, insufficient training. Machine: Tool wear, calibration issues. Material: Supplier variations, hardness differences. Method: Incorrect speeds, wrong feeds. Measurement: Gauge accuracy, measurement technique. Environment: Temperature fluctuations, humidity changes
Assistant: That's a comprehensive analysis. What would you like to do next?
User: Create a fishbone diagram
```

**AI Extraction Result:**
```json
{
  "cause_effect_data": {
    "problem": "Surface defects on machined parts",
    "main_categories": ["Man", "Machine", "Material", "Method", "Measurement", "Environment"],
    "sub_causes": {
      "Man": ["Operator fatigue", "Insufficient training"],
      "Machine": ["Tool wear", "Calibration issues"],
      "Material": ["Supplier variations", "Hardness differences"],
      "Method": ["Incorrect speeds", "Wrong feeds"],
      "Measurement": ["Gauge accuracy", "Measurement technique"],
      "Environment": ["Temperature fluctuations", "Humidity changes"]
    }
  }
}
```

## Benefits

### 1. **Intelligent Context Understanding**
- AI understands the relationship between different conversation turns
- Recognizes implicit data and specifications
- Handles complex, natural language descriptions

### 2. **Improved Data Extraction**
- More accurate extraction of structured data
- Better handling of various data formats
- Reduced false positives and missed data

### 3. **Enhanced User Experience**
- Users can provide data naturally in conversation
- No need to format data in specific patterns
- More intuitive interaction with the system

### 4. **Reliability**
- Fallback mechanism ensures system always works
- Graceful degradation when AI is unavailable
- Maintains backward compatibility

## Testing

Run the test script to see the enhanced system in action:

```bash
python test_ai_data_extraction.py
```

This will demonstrate:
- AI extraction for different chart types
- Fallback mechanism when AI fails
- Comparison between AI and regex extraction

## Technical Details

### Data Flow
1. **Input**: User query + conversation history
2. **AI Analysis**: Gemini extracts structured data
3. **Validation**: Check if data is sufficient for chart generation
4. **Chart Generation**: Use extracted data to create charts
5. **Fallback**: Use regex if AI fails

### Error Handling
- AI extraction failures are caught and logged
- Automatic fallback to regex extraction
- Graceful degradation maintains system functionality

### Performance
- AI extraction is asynchronous
- Fallback is fast and reliable
- System maintains responsiveness

## Future Enhancements

1. **Learning from User Feedback**: Improve AI prompts based on user corrections
2. **Multi-turn Data Collection**: Handle data spread across multiple conversations
3. **Data Validation**: AI-powered validation of extracted data
4. **Custom Extraction Rules**: User-defined extraction patterns
5. **Real-time Learning**: Continuous improvement of extraction accuracy

This implementation provides a robust, intelligent data extraction system that significantly enhances the user experience while maintaining system reliability through intelligent fallback mechanisms.
