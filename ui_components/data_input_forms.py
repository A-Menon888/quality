import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from data_extractor import DefectData, ProcessData, CauseEffectData

class DataInputForms:
    def _csv_or_excel_upload_entry(self) -> List[float]:
        """CSV or Excel upload for process measurements"""
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx', 'xls'])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.write("**Preview of uploaded data:**")
                st.dataframe(df.head())
                # Select column
                if len(df.columns) > 1:
                    column = st.selectbox("Select measurement column", df.columns)
                else:
                    column = df.columns[0]
                measurements = df[column].dropna().tolist()
                return measurements
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        return []
    """Forms for manual data entry and validation"""
    
    def __init__(self):
        self.defect_categories = ['Defect Type A', 'Defect Type B', 'Defect Type C', 'Defect Type D']
        self.cause_categories = ['Man', 'Machine', 'Material', 'Method', 'Measurement', 'Environment']
    
    def defect_data_form(self, existing_data: Optional[DefectData] = None) -> Optional[DefectData]:
        """Form for entering defect data"""
        
        st.markdown("### 📊 Defect Data Entry")
        
        # Initialize with existing data if available
        if existing_data:
            categories = existing_data.categories
            counts = existing_data.counts
        else:
            categories = []
            counts = []
        
        # Add new defect entries
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            new_category = st.text_input("Defect Category", placeholder="e.g., Surface Scratch")
        with col2:
            new_count = st.number_input("Count", min_value=0, value=0, step=1)
        with col3:
            if st.button("➕ Add", key="add_defect"):
                if new_category and new_count > 0:
                    categories.append(new_category)
                    counts.append(new_count)
                    st.rerun()
        
        # Display current data
        if categories:
            st.markdown("**Current Defect Data:**")
            df = pd.DataFrame({
                'Category': categories,
                'Count': counts
            })
            st.dataframe(df, use_container_width=True)
            
            # Remove entries
            if st.button("🗑️ Clear All Data"):
                categories.clear()
                counts.clear()
                st.rerun()
        
        # Generate DefectData object
        if categories and counts:
            total_defects = sum(counts)
            frequencies = [count/total_defects for count in counts]
            
            return DefectData(
                categories=categories,
                counts=counts,
                frequencies=frequencies,
                total_defects=total_defects,
                source="manual_input"
            )
        
        return None
    
    def process_data_form(self, existing_data: Optional[ProcessData] = None) -> Optional[ProcessData]:
        """Form for entering process measurement data"""
        st.markdown("### ⚙️ Process Data Entry")
        # Data input method selection
        input_method = st.radio(
            "Data Input Method",
            ["Manual Entry", "CSV/Excel Upload", "Paste from Excel"],
            horizontal=True
        )
        measurements = []
        specifications = {}
        if input_method == "Manual Entry":
            measurements = self._manual_measurement_entry(existing_data)
        elif input_method == "CSV/Excel Upload":
            measurements = self._csv_or_excel_upload_entry()
        elif input_method == "Paste from Excel":
            measurements = self._excel_paste_entry()
        # Specification limits
        st.markdown("**Specification Limits:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            usl = st.number_input("Upper Spec Limit (USL)", value=0.0, step=0.001, format="%.3f")
        with col2:
            lsl = st.number_input("Lower Spec Limit (LSL)", value=0.0, step=0.001, format="%.3f")
        with col3:
            target = st.number_input("Target Value", value=(usl + lsl) / 2 if usl and lsl else 0.0, step=0.001, format="%.3f")
        if usl and lsl:
            specifications = {'usl': usl, 'lsl': lsl, 'target': target}
        # Process name
        process_name = st.text_input("Process Name (Optional)", placeholder="e.g., Injection Molding")
        # Display current data
        if measurements:
            st.markdown("**Current Measurements:**")
            df = pd.DataFrame({
                'Sample': range(1, len(measurements) + 1),
                'Measurement': measurements
            })
            st.dataframe(df, use_container_width=True)
            # Basic statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Count", len(measurements))
            with col2:
                st.metric("Mean", f"{pd.Series(measurements).mean():.3f}")
            with col3:
                st.metric("Std Dev", f"{pd.Series(measurements).std():.3f}")
            with col4:
                st.metric("Range", f"{max(measurements) - min(measurements):.3f}")
        # Generate ProcessData object
        if measurements:
            return ProcessData(
                measurements=measurements,
                specifications=specifications,
                sample_size=len(measurements),
                process_name=process_name or None,
                source="file_upload" if input_method == "CSV/Excel Upload" else "manual_input"
            )
        return None
    
    def cause_effect_data_form(self, existing_data: Optional[CauseEffectData] = None) -> Optional[CauseEffectData]:
        """Form for entering cause-effect data"""
        
        st.markdown("### 🐟 Cause-Effect Data Entry")
        
        # Problem statement
        problem = st.text_area(
            "Problem Statement",
            value=existing_data.problem if existing_data else "",
            placeholder="Describe the problem you're trying to solve..."
        )
        
        # Main cause categories
        st.markdown("**Main Cause Categories (6M Framework):**")
        
        main_categories = []
        sub_causes = {}
        
        for category in self.cause_categories:
            with st.expander(f"🔍 {category}"):
                # Checkbox for including this category
                include_category = st.checkbox(f"Include {category}", key=f"include_{category}")
                
                if include_category:
                    main_categories.append(category)
                    
                    # Sub-causes for this category
                    st.write("**Sub-causes:**")
                    sub_cause_list = []
                    
                    # Add existing sub-causes
                    if existing_data and category in existing_data.sub_causes:
                        sub_cause_list = existing_data.sub_causes[category].copy()
                    
                    # Add new sub-causes
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_sub_cause = st.text_input(f"New {category} sub-cause", key=f"new_{category}")
                    with col2:
                        if st.button("Add", key=f"add_{category}"):
                            if new_sub_cause:
                                sub_cause_list.append(new_sub_cause)
                                st.rerun()
                    
                    # Display current sub-causes
                    if sub_cause_list:
                        for i, sub_cause in enumerate(sub_cause_list):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"• {sub_cause}")
                            with col2:
                                if st.button("Remove", key=f"remove_{category}_{i}"):
                                    sub_cause_list.pop(i)
                                    st.rerun()
                    
                    sub_causes[category] = sub_cause_list
        
        # Confidence level
        confidence = st.slider(
            "Confidence Level",
            min_value=0.0,
            max_value=1.0,
            value=existing_data.confidence if existing_data else 0.7,
            step=0.1,
            help="How confident are you in this cause analysis?"
        )
        
        # Generate CauseEffectData object
        if problem and main_categories:
            return CauseEffectData(
                problem=problem,
                main_categories=main_categories,
                sub_causes=sub_causes,
                confidence=confidence
            )
        
        return None
    
    def _manual_measurement_entry(self, existing_data: Optional[ProcessData] = None) -> List[float]:
        """Manual entry for process measurements"""
        
        measurements = existing_data.measurements if existing_data else []
        
        st.markdown("**Enter Measurements:**")
        
        # Single measurement entry
        col1, col2 = st.columns([3, 1])
        with col1:
            new_measurement = st.number_input("Measurement Value", value=0.0, step=0.001, format="%.3f")
        with col2:
            if st.button("Add Measurement"):
                measurements.append(new_measurement)
                st.rerun()
        
        # Bulk entry
        st.markdown("**Bulk Entry (comma-separated):**")
        bulk_input = st.text_area("Enter multiple values", placeholder="1.23, 1.24, 1.25, 1.26")
        if st.button("Add Bulk Measurements"):
            try:
                bulk_measurements = [float(x.strip()) for x in bulk_input.split(',') if x.strip()]
                measurements.extend(bulk_measurements)
                st.rerun()
            except ValueError:
                st.error("Please enter valid numbers separated by commas")
        
        return measurements
    
    def _csv_upload_entry(self) -> List[float]:
        """CSV upload for process measurements"""
        
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("**Preview of uploaded data:**")
                st.dataframe(df.head())
                
                # Select column
                if len(df.columns) > 1:
                    column = st.selectbox("Select measurement column", df.columns)
                else:
                    column = df.columns[0]
                
                measurements = df[column].dropna().tolist()
                return measurements
                
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
        
        return []
    
    def _excel_paste_entry(self) -> List[float]:
        """Excel paste entry for process measurements"""
        
        st.markdown("**Paste data from Excel:**")
        pasted_data = st.text_area(
            "Paste your data here (one value per line or comma-separated)",
            placeholder="1.23\n1.24\n1.25\n1.26"
        )
        
        if pasted_data:
            try:
                # Try line-separated first
                if '\n' in pasted_data:
                    measurements = [float(x.strip()) for x in pasted_data.split('\n') if x.strip()]
                else:
                    # Try comma-separated
                    measurements = [float(x.strip()) for x in pasted_data.split(',') if x.strip()]
                
                return measurements
                
            except ValueError:
                st.error("Please enter valid numbers (one per line or comma-separated)")
        
        return []
    
    def data_validation_summary(self, data: Any, tool_type: str) -> Dict[str, Any]:
        """Display data validation summary"""
        
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        if tool_type == 'defect_data' and isinstance(data, DefectData):
            if data.total_defects == 0:
                validation_result['errors'].append("No defects found")
                validation_result['is_valid'] = False
            
            if len(data.categories) < 3:
                validation_result['warnings'].append("Consider adding more defect categories for better analysis")
            
            if data.total_defects < 10:
                validation_result['warnings'].append("Low sample size may affect statistical significance")
        
        elif tool_type == 'process_data' and isinstance(data, ProcessData):
            if len(data.measurements) < 30:
                validation_result['warnings'].append("Sample size less than 30 may affect process capability calculations")
            
            if not data.specifications:
                validation_result['warnings'].append("Specification limits not provided")
                validation_result['suggestions'].append("Add USL and LSL for process capability analysis")
        
        elif tool_type == 'cause_effect_data' and isinstance(data, CauseEffectData):
            if not data.main_categories:
                validation_result['errors'].append("No cause categories identified")
                validation_result['is_valid'] = False
            
            if len(data.main_categories) < 2:
                validation_result['warnings'].append("Consider using more cause categories for comprehensive analysis")
        
        return validation_result