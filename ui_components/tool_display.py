import streamlit as st
import base64
import io
from typing import Dict, Any, Optional, List
import pandas as pd
from chart_generators import (
    ParetoChartGenerator, FishboneDiagramGenerator, 
    ControlChartGenerator, HistogramGenerator, ProcessCapabilityGenerator
)

class ToolDisplayComponent:
    """Component for displaying generated QC tools and charts"""
    
    def __init__(self):
        self.chart_generators = {
            'pareto_chart': ParetoChartGenerator(),
            'fishbone_diagram': FishboneDiagramGenerator(),
            'control_chart': ControlChartGenerator(),
            'histogram': HistogramGenerator(),
            'process_capability': ProcessCapabilityGenerator()
        }
    
    def display_generated_tool(self, tool_result: Dict[str, Any], 
                             tool_type: str, 
                             show_statistics: bool = False,
                             show_customization: bool = False) -> None:
        """Display a generated QC tool with options"""
        
        if not tool_result.get('success', False):
            st.error(f"❌ Tool generation failed: {tool_result.get('error_message', 'Unknown error')}")
            return
        
        # Display the chart
        if tool_result.get('chart_data'):
            self._display_chart(tool_result['chart_data'], tool_type)
        
        # Display statistics if available
        if show_statistics and tool_result.get('statistics'):
            self._display_statistics(tool_result['statistics'], tool_type)
        
        # Display customization options
        if show_customization:
            self._display_customization_options(tool_type, tool_result)
    
    def _display_chart(self, chart_bytes: bytes, tool_type: str) -> None:
        """Display the generated chart"""
        
        # Convert bytes to base64 for display
        chart_base64 = base64.b64encode(chart_bytes).decode()
        
        # Display based on tool type
        if tool_type == 'pareto_chart':
            st.markdown("### 📊 Pareto Chart Analysis")
            st.image(chart_bytes, use_container_width=True, caption="Pareto Chart - Defect Analysis")
        
        elif tool_type == 'fishbone_diagram':
            st.markdown("### 🐟 Fishbone Diagram")
            st.image(chart_bytes, use_container_width=True, caption="Fishbone Diagram - Root Cause Analysis")
        
        elif tool_type == 'control_chart':
            st.markdown("### �� Control Chart")
            st.image(chart_bytes, use_container_width=True, caption="Control Chart - Process Monitoring")
        
        elif tool_type == 'histogram':
            st.markdown("### 📊 Histogram Analysis")
            st.image(chart_bytes, use_container_width=True, caption="Histogram - Process Distribution")
        
        elif tool_type == 'process_capability':
            st.markdown("### ⚙️ Process Capability Analysis")
            st.image(chart_bytes, use_container_width=True, caption="Process Capability Analysis")
        
        else:
            st.image(chart_bytes, use_container_width=True, caption=f"Generated {tool_type.replace('_', ' ').title()}")
    
    def _display_statistics(self, statistics: Dict[str, Any], tool_type: str) -> None:
        """Display statistics for the generated tool"""
        
        st.markdown("---")
        st.markdown("### 📈 Statistics & Analysis")
        
        if tool_type == 'pareto_chart':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Defects", statistics.get('total_defects', 0))
            with col2:
                st.metric("Categories", statistics.get('categories', 0))
            with col3:
                st.metric("Top Category %", f"{statistics.get('top_category_percentage', 0):.1f}%")
            
            # Pareto 80/20 analysis
            pareto_80 = statistics.get('pareto_80_categories', 0)
            st.info(f"�� **Pareto 80/20 Rule**: {pareto_80} categories account for 80% of defects")
        
        elif tool_type == 'fishbone_diagram':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Main Categories", statistics.get('main_categories', 0))
            with col2:
                st.metric("Total Sub-Causes", statistics.get('total_sub_causes', 0))
            with col3:
                st.metric("Confidence", f"{statistics.get('confidence', 0)*100:.1f}%")
        
        elif tool_type == 'control_chart':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sample Size", statistics.get('sample_size', 0))
            with col2:
                st.metric("Mean", f"{statistics.get('mean', 0):.3f}")
            with col3:
                st.metric("Std Dev", f"{statistics.get('std_dev', 0):.3f}")
            
            # Process capability status
            if statistics.get('process_capable', False):
                st.success("✅ Process is in control")
            else:
                st.warning(f"⚠️ {statistics.get('out_of_control_points', 0)} points out of control")
        
        elif tool_type == 'histogram':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sample Size", statistics.get('sample_size', 0))
            with col2:
                st.metric("Mean", f"{statistics.get('mean', 0):.3f}")
            with col3:
                st.metric("Std Dev", f"{statistics.get('std_dev', 0):.3f}")
            
            # Distribution analysis
            if statistics.get('is_normal'):
                st.success("✅ Data appears to follow normal distribution")
            else:
                st.warning("⚠️ Data may not follow normal distribution")
        
        elif tool_type == 'process_capability':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cpk", f"{statistics.get('cpk', 0):.3f}")
            with col2:
                st.metric("Sigma Level", f"{statistics.get('sigma_level', 0):.2f}σ")
            with col3:
                st.metric("PPM", f"{statistics.get('ppm', 0):.0f}")
            
            # Capability assessment
            if statistics.get('is_capable', False):
                st.success("✅ Process is capable")
            else:
                st.error("❌ Process needs improvement")
    
    def _display_customization_options(self, tool_type: str, tool_result: Dict[str, Any]) -> None:
        """Display customization options for the tool"""
        
        st.markdown("---")
        st.markdown("### ⚙️ Customization Options")
        
        if tool_type == 'pareto_chart':
            col1, col2 = st.columns(2)
            with col1:
                show_80_20 = st.checkbox("Show 80/20 Line", value=True)
                show_cumulative = st.checkbox("Show Cumulative %", value=True)
            with col2:
                show_values = st.checkbox("Show Value Labels", value=True)
                show_stats = st.checkbox("Show Statistics Box", value=True)
            
            if st.button("🔄 Regenerate Chart", key="regen_pareto"):
                # This would trigger regeneration with new parameters
                st.rerun()
        
        elif tool_type == 'fishbone_diagram':
            col1, col2 = st.columns(2)
            with col1:
                show_sub_causes = st.checkbox("Show Sub-Causes", value=True)
                show_connections = st.checkbox("Show Connections", value=True)
            with col2:
                show_legend = st.checkbox("Show Legend", value=True)
            
            if st.button("🔄 Regenerate Diagram", key="regen_fishbone"):
                st.rerun()
        
        elif tool_type == 'control_chart':
            col1, col2 = st.columns(2)
            with col1:
                subgroup_size = st.selectbox("Subgroup Size", [2, 3, 4, 5, 6, 7, 8, 9, 10], index=4)
                show_spec_limits = st.checkbox("Show Spec Limits", value=True)
            with col2:
                show_trend_lines = st.checkbox("Show Trend Lines", value=True)
                show_moving_range = st.checkbox("Show Moving Range", value=True)
            
            if st.button("🔄 Regenerate Chart", key="regen_control"):
                st.rerun()
    
    def display_data_table(self, data: Any, tool_type: str) -> None:
        """Display data in a table format"""
        
        st.markdown("---")
        st.markdown("### �� Data Table")
        
        if tool_type == 'pareto_chart' and hasattr(data, 'categories'):
            # Create Pareto table
            df = pd.DataFrame({
                'Category': data.categories,
                'Count': data.counts,
                'Frequency (%)': [f*100 for f in data.frequencies],
                'Cumulative %': [sum(data.frequencies[:i+1])*100 for i in range(len(data.frequencies))]
            })
            st.dataframe(df, use_container_width=True)
        
        elif tool_type == 'control_chart' and hasattr(data, 'measurements'):
            # Create measurements table
            df = pd.DataFrame({
                'Sample': range(1, len(data.measurements) + 1),
                'Measurement': data.measurements
            })
            st.dataframe(df, use_container_width=True)
        
        elif tool_type == 'process_capability' and hasattr(data, 'measurements'):
            # Create capability summary table
            df = pd.DataFrame({
                'Sample': range(1, len(data.measurements) + 1),
                'Measurement': data.measurements,
                'Within Spec': ['Yes' if data.specifications.get('lsl', 0) <= m <= data.specifications.get('usl', 100) else 'No' for m in data.measurements]
            })
            st.dataframe(df, use_container_width=True)
    
    def display_tool_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """Display tool recommendations"""
        
        if not recommendations:
            return
        
        st.markdown("---")
        st.markdown("### 💡 Recommended Actions")
        
        for i, rec in enumerate(recommendations):
            with st.expander(f"Recommendation {i+1}: {rec.get('title', 'Action Item')}"):
                st.write(rec.get('description', ''))
                if rec.get('priority'):
                    st.write(f"**Priority**: {rec['priority']}")
                if rec.get('timeline'):
                    st.write(f"**Timeline**: {rec['timeline']}")