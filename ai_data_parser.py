import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional, Union
from data_extractor import DefectData, ProcessData, CauseEffectData, QualityMetrics, DataExtractor
from tool_recommender import enhanced_tool_lookup

class AIDataParser:
    """AI-powered data extraction and interpretation using Gemini"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self.model = genai.GenerativeModel(model_name)
        self.data_extractor = DataExtractor()
    
    def extract_structured_data(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Extract structured data from natural language using AI"""
        
        prompt = f"""
        You are a quality assurance data extraction expert. Extract structured data from the user's input for QC tool generation.

        User Input: "{user_input}"
        Context: "{context}"

        Extract the following types of data if present:

        1. DEFECT DATA:
        - Categories of defects/issues/problems
        - Counts/frequencies for each category
        - Time period if mentioned

        2. PROCESS DATA:
        - Measurement values
        - Specification limits (USL, LSL, Target)
        - Sample size information
        - Process name or description

        3. CAUSE-EFFECT DATA:
        - Problem statement
        - Main cause categories (Man, Machine, Material, Method, Measurement, Environment)
        - Specific sub-causes for each category

        4. QUALITY METRICS:
        - Cp/Cpk values
        - Yield percentages
        - Defect rates
        - Sigma levels

        Return ONLY a JSON object with this structure:
        {{
            "defect_data": {{
                "categories": ["category1", "category2"],
                "counts": [10, 5],
                "time_period": "optional"
            }},
            "process_data": {{
                "measurements": [1.2, 1.3, 1.1],
                "specifications": {{
                    "usl": 1.5,
                    "lsl": 1.0,
                    "target": 1.25
                }},
                "process_name": "optional"
            }},
            "cause_effect_data": {{
                "problem": "problem description",
                "main_categories": ["Man", "Machine"],
                "sub_causes": {{
                    "Man": ["Training", "Fatigue"],
                    "Machine": ["Wear", "Calibration"]
                }}
            }},
            "quality_metrics": [
                {{
                    "metric_name": "Cp",
                    "value": 1.33,
                    "unit": null
                }}
            ]
        }}

        If a data type is not present, set it to null. Be precise and only extract what's clearly stated.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up the response to extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            # Parse JSON
            extracted_data = json.loads(result_text)
            
            # Convert to proper data structures
            structured_data = self._convert_to_data_structures(extracted_data)
            
            return {
                'success': True,
                'data': structured_data,
                'raw_extraction': extracted_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"AI extraction failed: {str(e)}",
                'data': None
            }
    
    def _convert_to_data_structures(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert extracted JSON to proper data structures"""
        
        result = {}
        
        # Convert defect data
        if extracted_data.get('defect_data'):
            defect_info = extracted_data['defect_data']
            if defect_info.get('categories') and defect_info.get('counts'):
                total_defects = sum(defect_info['counts'])
                frequencies = [count/total_defects for count in defect_info['counts']]
                
                result['defect_data'] = DefectData(
                    categories=defect_info['categories'],
                    counts=defect_info['counts'],
                    frequencies=frequencies,
                    total_defects=total_defects,
                    time_period=defect_info.get('time_period'),
                    source="ai_extraction"
                )
        
        # Convert process data
        if extracted_data.get('process_data'):
            process_info = extracted_data['process_data']
            if process_info.get('measurements'):
                result['process_data'] = ProcessData(
                    measurements=process_info['measurements'],
                    specifications=process_info.get('specifications', {}),
                    sample_size=len(process_info['measurements']),
                    process_name=process_info.get('process_name'),
                    source="ai_extraction"
                )
        
        # Convert cause-effect data
        if extracted_data.get('cause_effect_data'):
            cause_info = extracted_data['cause_effect_data']
            if cause_info.get('problem') or cause_info.get('main_categories'):
                result['cause_effect_data'] = CauseEffectData(
                    problem=cause_info.get('problem', 'Unspecified problem'),
                    main_categories=cause_info.get('main_categories', []),
                    sub_causes=cause_info.get('sub_causes', {}),
                    confidence=0.8  # High confidence for AI extraction
                )
        
        # Convert quality metrics
        if extracted_data.get('quality_metrics'):
            metrics_info = extracted_data['quality_metrics']
            result['quality_metrics'] = []
            for metric in metrics_info:
                result['quality_metrics'].append(QualityMetrics(
                    metric_name=metric.get('metric_name', 'Unknown'),
                    value=metric.get('value', 0),
                    unit=metric.get('unit'),
                    source="ai_extraction"
                ))
        
        return result
    
    def suggest_data_improvements(self, user_input: str, tool_type: str) -> Dict[str, Any]:
        """Suggest improvements to user input for better tool generation"""
        
        if tool_type not in enhanced_tool_lookup:
            return {'suggestions': [], 'improved_input': user_input}
        
        tool_info = enhanced_tool_lookup[tool_type]
        required_data = tool_info.get('required_data')
        min_data_points = tool_info.get('min_data_points', 0)
        
        prompt = f"""
        The user wants to generate a {tool_info['tool']} but their input may be incomplete.
        
        User Input: "{user_input}"
        Required Data Type: {required_data}
        Minimum Data Points Needed: {min_data_points}
        
        Analyze their input and suggest specific improvements to make it suitable for generating the tool.
        Focus on what data is missing or unclear.
        
        Return a JSON object with:
        {{
            "is_sufficient": true/false,
            "missing_data": ["list of missing data points"],
            "unclear_data": ["list of unclear data points"],
            "suggestions": ["specific suggestions for improvement"],
            "improved_input": "suggested improved version of their input"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up the response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            suggestions = json.loads(result_text)
            return suggestions
            
        except Exception as e:
            return {
                'is_sufficient': False,
                'missing_data': ['Unable to analyze'],
                'unclear_data': [],
                'suggestions': [f'Error analyzing input: {str(e)}'],
                'improved_input': user_input
            }
    
    def generate_data_collection_questions(self, tool_type: str, current_data: Dict[str, Any]) -> List[str]:
        """Generate questions to collect missing data for tool generation"""
        
        if tool_type not in enhanced_tool_lookup:
            return []
        
        tool_info = enhanced_tool_lookup[tool_type]
        required_data = tool_info.get('required_data')
        min_data_points = tool_info.get('min_data_points', 0)
        
        questions = []
        
        if required_data == 'defect_data':
            if not current_data.get('defect_data'):
                questions.extend([
                    "What types of defects or problems are you seeing?",
                    "How many of each type of defect occurred?",
                    "What time period does this data cover?"
                ])
            elif len(current_data['defect_data'].categories) < min_data_points:
                questions.append(f"Can you provide more defect categories? I need at least {min_data_points} different types.")
        
        elif required_data == 'process_data':
            if not current_data.get('process_data'):
                questions.extend([
                    "What are the actual measurement values from your process?",
                    "What are the specification limits (USL and LSL)?",
                    "What is the target value for this process?"
                ])
            elif len(current_data['process_data'].measurements) < min_data_points:
                questions.append(f"Can you provide more measurement data? I need at least {min_data_points} data points.")
        
        elif required_data == 'cause_effect_data':
            if not current_data.get('cause_effect_data'):
                questions.extend([
                    "What is the specific problem you're trying to solve?",
                    "What are the main cause categories (Man, Machine, Material, Method, Measurement, Environment)?",
                    "What specific sub-causes can you identify for each category?"
                ])
            elif len(current_data['cause_effect_data'].main_categories) < min_data_points:
                questions.append(f"Can you identify more cause categories? I need at least {min_data_points} different categories.")
        
        return questions
    
    def validate_extracted_data(self, data: Dict[str, Any], tool_type: str) -> Dict[str, Any]:
        """Validate extracted data against tool requirements"""
        
        if tool_type not in enhanced_tool_lookup:
            return {'is_valid': False, 'errors': ['Unknown tool type']}
        
        tool_info = enhanced_tool_lookup[tool_type]
        required_data = tool_info.get('required_data')
        min_data_points = tool_info.get('min_data_points', 0)
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        if required_data == 'defect_data':
            defect_data = data.get('defect_data')
            if not defect_data:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Defect data is required for this tool")
            elif len(defect_data.categories) < min_data_points:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Need at least {min_data_points} defect categories")
            elif defect_data.total_defects == 0:
                validation_result['is_valid'] = False
                validation_result['errors'].append("No defects found in data")
        
        elif required_data == 'process_data':
            process_data = data.get('process_data')
            if not process_data:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Process data is required for this tool")
            elif len(process_data.measurements) < min_data_points:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Need at least {min_data_points} measurement points")
            elif not process_data.specifications:
                validation_result['warnings'].append("Specification limits not provided")
        
        elif required_data == 'cause_effect_data':
            cause_data = data.get('cause_effect_data')
            if not cause_data:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Cause-effect data is required for this tool")
            elif len(cause_data.main_categories) < min_data_points:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Need at least {min_data_points} cause categories")
        
        return validation_result