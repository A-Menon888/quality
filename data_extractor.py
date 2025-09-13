import re
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class DefectData:
    """Structure for defect-related data"""
    categories: List[str]
    counts: List[int]
    frequencies: List[float]
    total_defects: int
    time_period: Optional[str] = None
    source: Optional[str] = None

@dataclass
class ProcessData:
    """Structure for process measurement data"""
    measurements: List[float]
    specifications: Dict[str, float]  # {'usl': 10.5, 'lsl': 9.5, 'target': 10.0}
    sample_size: int
    time_series: Optional[List[datetime]] = None
    process_name: Optional[str] = None
    source: Optional[str] = None

@dataclass
class CauseEffectData:
    """Structure for cause-effect relationship data"""
    problem: str
    main_categories: List[str]  # ['Man', 'Machine', 'Material', 'Method', 'Measurement', 'Environment']
    sub_causes: Dict[str, List[str]]  # {'Man': ['Training', 'Fatigue'], 'Machine': ['Wear', 'Calibration']}
    confidence: float = 0.0

@dataclass
class QualityMetrics:
    """Structure for quality metrics data"""
    metric_name: str
    value: float
    target: Optional[float] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None
    trend: Optional[str] = None  # 'increasing', 'decreasing', 'stable'

class DataExtractor:
    """Extracts and structures data from user input for QC tool generation"""
    
    def __init__(self):
        self.defect_patterns = [
            r'(\d+)\s+(?:defects?|issues?|problems?|failures?)\s+(?:in|of|for)\s+([^,]+)',
            r'([^,]+):\s*(\d+)\s*(?:times?|occurrences?|instances?)',
            r'(\d+)\s+(?:times?|occurrences?)\s+(?:of|for)\s+([^,]+)',
            r'([^,]+)\s+(\d+)\s*(?:defects?|issues?|problems?)'
        ]
        
        self.process_patterns = [
            r'specification[s]?\s*:?\s*([0-9.]+)\s*[-–]\s*([0-9.]+)',
            r'usl\s*:?\s*([0-9.]+).*lsl\s*:?\s*([0-9.]+)',
            r'target\s*:?\s*([0-9.]+)',
            r'measurement[s]?\s*:?\s*([0-9.,\s]+)'
        ]
        
        self.cause_patterns = [
            r'(?:cause|reason|source)\s*:?\s*([^,]+)',
            r'(?:due to|because of|caused by)\s+([^,]+)',
            r'(?:man|machine|material|method|measurement|environment)\s*:?\s*([^,]+)'
        ]

    def extract_defect_data(self, text: str) -> Optional[DefectData]:
        """Extract defect data from text input"""
        try:
            categories = []
            counts = []
            
            # Try different patterns to extract defect data
            for pattern in self.defect_patterns:
                matches = re.findall(pattern, text.lower())
                for match in matches:
                    if len(match) == 2:
                        try:
                            count = int(match[0])
                            category = match[1].strip()
                            categories.append(category)
                            counts.append(count)
                        except ValueError:
                            try:
                                count = int(match[1])
                                category = match[0].strip()
                                categories.append(category)
                                counts.append(count)
                            except ValueError:
                                continue
            
            if not categories or not counts:
                return None
                
            total_defects = sum(counts)
            frequencies = [count/total_defects for count in counts]
            
            return DefectData(
                categories=categories,
                counts=counts,
                frequencies=frequencies,
                total_defects=total_defects,
                source="user_input"
            )
            
        except Exception as e:
            print(f"Error extracting defect data: {e}")
            return None

    def extract_process_data(self, text: str) -> Optional[ProcessData]:
        """Extract process measurement data from text input"""
        try:
            measurements = []
            specifications = {}
            
            # Extract measurements
            measurement_matches = re.findall(r'([0-9.]+)', text)
            measurements = [float(m) for m in measurement_matches if float(m) > 0]
            
            # Extract specifications
            spec_matches = re.findall(self.process_patterns[0], text.lower())
            if spec_matches:
                for match in spec_matches:
                    try:
                        usl = float(match[0])
                        lsl = float(match[1])
                        specifications['usl'] = usl
                        specifications['lsl'] = lsl
                        specifications['target'] = (usl + lsl) / 2
                    except ValueError:
                        continue
            
            # Extract target if not already set
            target_matches = re.findall(self.process_patterns[2], text.lower())
            if target_matches and 'target' not in specifications:
                specifications['target'] = float(target_matches[0])
            
            if not measurements:
                return None
                
            return ProcessData(
                measurements=measurements,
                specifications=specifications,
                sample_size=len(measurements),
                source="user_input"
            )
            
        except Exception as e:
            print(f"Error extracting process data: {e}")
            return None

    def extract_cause_effect_data(self, text: str) -> Optional[CauseEffectData]:
        """Extract cause-effect relationship data from text input"""
        try:
            problem = ""
            main_categories = []
            sub_causes = {}
            
            # Extract problem statement
            problem_patterns = [
                r'problem\s*:?\s*([^,]+)',
                r'issue\s*:?\s*([^,]+)',
                r'defect\s*:?\s*([^,]+)',
                r'failure\s*:?\s*([^,]+)'
            ]
            
            for pattern in problem_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    problem = match.group(1).strip()
                    break
            
            # Extract causes by category
            categories = ['man', 'machine', 'material', 'method', 'measurement', 'environment']
            for category in categories:
                pattern = f'{category}\\s*:?\\s*([^,]+)'
                matches = re.findall(pattern, text.lower())
                if matches:
                    main_categories.append(category.title())
                    sub_causes[category.title()] = [m.strip() for m in matches]
            
            if not problem and not main_categories:
                return None
                
            return CauseEffectData(
                problem=problem or "Unspecified problem",
                main_categories=main_categories,
                sub_causes=sub_causes,
                confidence=0.7 if main_categories else 0.3
            )
            
        except Exception as e:
            print(f"Error extracting cause-effect data: {e}")
            return None

    def extract_quality_metrics(self, text: str) -> List[QualityMetrics]:
        """Extract quality metrics from text input"""
        try:
            metrics = []
            
            # Common quality metrics patterns
            metric_patterns = [
                r'(?:cp|cpk|cpu|cpl)\s*:?\s*([0-9.]+)',
                r'(?:yield|first pass yield)\s*:?\s*([0-9.]+)%?',
                r'(?:defect rate|dpu|dpo|dpmu)\s*:?\s*([0-9.]+)',
                r'(?:sigma|sigma level)\s*:?\s*([0-9.]+)'
            ]
            
            metric_names = ['Cp/Cpk', 'Yield', 'Defect Rate', 'Sigma Level']
            
            for i, pattern in enumerate(metric_patterns):
                matches = re.findall(pattern, text.lower())
                for match in matches:
                    try:
                        value = float(match)
                        metrics.append(QualityMetrics(
                            metric_name=metric_names[i],
                            value=value,
                            unit='%' if 'yield' in pattern else None
                        ))
                    except ValueError:
                        continue
            
            return metrics
            
        except Exception as e:
            print(f"Error extracting quality metrics: {e}")
            return []

    def validate_data(self, data: Union[DefectData, ProcessData, CauseEffectData, List[QualityMetrics]]) -> Dict[str, Any]:
        """Validate extracted data and return validation results"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        if isinstance(data, DefectData):
            if data.total_defects == 0:
                validation_result['errors'].append("No defects found in data")
                validation_result['is_valid'] = False
            if len(data.categories) != len(data.counts):
                validation_result['errors'].append("Mismatch between categories and counts")
                validation_result['is_valid'] = False
            if data.total_defects < 5:
                validation_result['warnings'].append("Low sample size may affect statistical significance")
                
        elif isinstance(data, ProcessData):
            if len(data.measurements) < 30:
                validation_result['warnings'].append("Sample size less than 30 may affect process capability calculations")
            if not data.specifications:
                validation_result['warnings'].append("No specification limits found")
                validation_result['suggestions'].append("Consider adding USL and LSL for process capability analysis")
                
        elif isinstance(data, CauseEffectData):
            if not data.main_categories:
                validation_result['warnings'].append("No cause categories identified")
                validation_result['suggestions'].append("Consider using 6M framework: Man, Machine, Material, Method, Measurement, Environment")
                
        return validation_result

    def clean_and_normalize_data(self, data: Union[DefectData, ProcessData, CauseEffectData]) -> Union[DefectData, ProcessData, CauseEffectData]:
        """Clean and normalize extracted data"""
        if isinstance(data, DefectData):
            # Remove empty categories and corresponding counts
            clean_categories = []
            clean_counts = []
            for cat, count in zip(data.categories, data.counts):
                if cat.strip() and count > 0:
                    clean_categories.append(cat.strip().title())
                    clean_counts.append(count)
            
            if clean_categories:
                total = sum(clean_counts)
                frequencies = [count/total for count in clean_counts]
                data.categories = clean_categories
                data.counts = clean_counts
                data.frequencies = frequencies
                data.total_defects = total
                
        elif isinstance(data, ProcessData):
            # Remove outliers and invalid measurements
            measurements = [m for m in data.measurements if m > 0 and not pd.isna(m)]
            if measurements:
                data.measurements = measurements
                data.sample_size = len(measurements)
                
        return data