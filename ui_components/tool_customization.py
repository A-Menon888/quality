import streamlit as st
from typing import Dict, Any, List, Optional
import json

class ToolCustomizationPanel:
    """Panel for customizing QC tool parameters and appearance"""
    
    def __init__(self):
        self.default_settings = {
            'pareto_chart': {
                'show_80_20_line': True,
                'show_cumulative_percentage': True,
                'show_value_labels': True,
                'show_statistics': True,
                'color_scheme': 'default',
                'chart_size': 'medium'
            },
            'fishbone_diagram': {
                'show_sub_causes': True,
                'show_connections': True,
                'show_legend': True,
                'diagram_style': 'standard',
                'color_scheme': 'default'
            },
            'control_chart': {
                'subgroup_size': 5,
                'show_spec_limits': True,
                'show_trend_lines': True,
                'show_moving_range': True,
                'chart_type': 'xbar_r'
            },
            'histogram': {
                'bins': 'auto',
                'show_normal_curve': True,
                'show_statistics': True,
                'show_spec_limits': True,
                'distribution_test': True
            },
            'process_capability': {
                'show_histogram': True,
                'show_control_limits': True,
                'show_capability_zone': True,
                'capability_grade': True,
                'sigma_level': True
            }
        }
    
    def render_customization_panel(self, tool_type: str, 
                                 current_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Render customization panel for specific tool type"""
        
        if tool_type not in self.default_settings:
            st.error(f"Customization not available for {tool_type}")
            return {}
        
        settings = current_settings or self.default_settings[tool_type].copy()
        
        st.markdown("### ⚙️ Tool Customization")
        
        if tool_type == 'pareto_chart':
            return self._pareto_customization(settings)
        elif tool_type == 'fishbone_diagram':
            return self._fishbone_customization(settings)
        elif tool_type == 'control_chart':
            return self._control_chart_customization(settings)
        elif tool_type == 'histogram':
            return self._histogram_customization(settings)
        elif tool_type == 'process_capability':
            return self._capability_customization(settings)
        
        return settings
    
    def _pareto_customization(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Customization options for Pareto chart"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Display Options:**")
            settings['show_80_20_line'] = st.checkbox(
                "Show 80/20 Line", 
                value=settings['show_80_20_line'],
                help="Display the Pareto 80% line"
            )
            settings['show_cumulative_percentage'] = st.checkbox(
                "Show Cumulative %", 
                value=settings['show_cumulative_percentage'],
                help="Display cumulative percentage labels"
            )
            settings['show_value_labels'] = st.checkbox(
                "Show Value Labels", 
                value=settings['show_value_labels'],
                help="Display count and percentage on bars"
            )
            settings['show_statistics'] = st.checkbox(
                "Show Statistics Box", 
                value=settings['show_statistics'],
                help="Display summary statistics"
            )
        
        with col2:
            st.markdown("**Appearance:**")
            settings['color_scheme'] = st.selectbox(
                "Color Scheme",
                ['default', 'blue', 'green', 'red', 'purple', 'orange'],
                index=['default', 'blue', 'green', 'red', 'purple', 'orange'].index(settings['color_scheme'])
            )
            settings['chart_size'] = st.selectbox(
                "Chart Size",
                ['small', 'medium', 'large'],
                index=['small', 'medium', 'large'].index(settings['chart_size'])
            )
        
        return settings
    
    def _fishbone_customization(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Customization options for Fishbone diagram"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Display Options:**")
            settings['show_sub_causes'] = st.checkbox(
                "Show Sub-Causes", 
                value=settings['show_sub_causes'],
                help="Display detailed sub-causes for each category"
            )
            settings['show_connections'] = st.checkbox(
                "Show Connections", 
                value=settings['show_connections'],
                help="Display connection lines between related causes"
            )
            settings['show_legend'] = st.checkbox(
                "Show Legend", 
                value=settings['show_legend'],
                help="Display legend explaining diagram elements"
            )
        
        with col2:
            st.markdown("**Appearance:**")
            settings['diagram_style'] = st.selectbox(
                "Diagram Style",
                ['standard', 'minimal', 'detailed'],
                index=['standard', 'minimal', 'detailed'].index(settings['diagram_style'])
            )
            settings['color_scheme'] = st.selectbox(
                "Color Scheme",
                ['default', 'blue', 'green', 'red', 'purple', 'orange'],
                index=['default', 'blue', 'green', 'red', 'purple', 'orange'].index(settings['color_scheme'])
            )
        
        return settings
    
    def _control_chart_customization(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Customization options for Control chart"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Chart Configuration:**")
            settings['chart_type'] = st.selectbox(
                "Chart Type",
                ['xbar_r', 'individuals', 'p_chart', 'np_chart', 'c_chart', 'u_chart'],
                index=['xbar_r', 'individuals', 'p_chart', 'np_chart', 'c_chart', 'u_chart'].index(settings['chart_type'])
            )
            settings['subgroup_size'] = st.selectbox(
                "Subgroup Size",
                [2, 3, 4, 5, 6, 7, 8, 9, 10],
                index=[2, 3, 4, 5, 6, 7, 8, 9, 10].index(settings['subgroup_size'])
            )
        
        with col2:
            st.markdown("**Display Options:**")
            settings['show_spec_limits'] = st.checkbox(
                "Show Spec Limits", 
                value=settings['show_spec_limits'],
                help="Display specification limits"
            )
            settings['show_trend_lines'] = st.checkbox(
                "Show Trend Lines", 
                value=settings['show_trend_lines'],
                help="Display trend analysis lines"
            )
            settings['show_moving_range'] = st.checkbox(
                "Show Moving Range", 
                value=settings['show_moving_range'],
                help="Display moving range chart"
            )
        
        return settings
    
    def _histogram_customization(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Customization options for Histogram"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Display Options:**")
            settings['show_normal_curve'] = st.checkbox(
                "Show Normal Curve", 
                value=settings['show_normal_curve'],
                help="Overlay normal distribution curve"
            )
            settings['show_statistics'] = st.checkbox(
                "Show Statistics", 
                value=settings['show_statistics'],
                help="Display statistical summary"
            )
            settings['show_spec_limits'] = st.checkbox(
                "Show Spec Limits", 
                value=settings['show_spec_limits'],
                help="Display specification limits"
            )
            settings['distribution_test'] = st.checkbox(
                "Distribution Test", 
                value=settings['distribution_test'],
                help="Perform normality test"
            )
        
        with col2:
            st.markdown("**Configuration:**")
            settings['bins'] = st.selectbox(
                "Bin Configuration",
                ['auto', 'sturges', 'fd', 'scott', 'sqrt'],
                index=['auto', 'sturges', 'fd', 'scott', 'sqrt'].index(settings['bins'])
            )
        
        return settings
    
    def _capability_customization(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Customization options for Process Capability"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Display Options:**")
            settings['show_histogram'] = st.checkbox(
                "Show Histogram", 
                value=settings['show_histogram'],
                help="Display histogram with normal curve"
            )
            settings['show_control_limits'] = st.checkbox(
                "Show Control Limits", 
                value=settings['show_control_limits'],
                help="Display control chart limits"
            )
            settings['show_capability_zone'] = st.checkbox(
                "Show Capability Zone", 
                value=settings['show_capability_zone'],
                help="Highlight area within specification limits"
            )
        
        with col2:
            st.markdown("**Analysis Options:**")
            settings['capability_grade'] = st.checkbox(
                "Show Capability Grade", 
                value=settings['capability_grade'],
                help="Display capability grade assessment"
            )
            settings['sigma_level'] = st.checkbox(
                "Show Sigma Level", 
                value=settings['sigma_level'],
                help="Display sigma level calculation"
            )
        
        return settings
    
    def save_customization_preset(self, tool_type: str, settings: Dict[str, Any], 
                                preset_name: str) -> bool:
        """Save customization settings as a preset"""
        
        try:
            # In a real implementation, this would save to a database or file
            # For now, we'll use session state
            if 'customization_presets' not in st.session_state:
                st.session_state.customization_presets = {}
            
            if tool_type not in st.session_state.customization_presets:
                st.session_state.customization_presets[tool_type] = {}
            
            st.session_state.customization_presets[tool_type][preset_name] = settings
            return True
            
        except Exception as e:
            st.error(f"Failed to save preset: {str(e)}")
            return False
    
    def load_customization_preset(self, tool_type: str, preset_name: str) -> Optional[Dict[str, Any]]:
        """Load customization settings from a preset"""
        
        try:
            if 'customization_presets' in st.session_state:
                if tool_type in st.session_state.customization_presets:
                    if preset_name in st.session_state.customization_presets[tool_type]:
                        return st.session_state.customization_presets[tool_type][preset_name]
            
            return None
            
        except Exception as e:
            st.error(f"Failed to load preset: {str(e)}")
            return None
    
    def get_available_presets(self, tool_type: str) -> List[str]:
        """Get list of available presets for a tool type"""
        
        if 'customization_presets' in st.session_state:
            if tool_type in st.session_state.customization_presets:
                return list(st.session_state.customization_presets[tool_type].keys())
        
        return []
    
    def export_customization(self, tool_type: str, settings: Dict[str, Any]) -> str:
        """Export customization settings as JSON"""
        
        export_data = {
            'tool_type': tool_type,
            'settings': settings,
            'export_timestamp': st.session_state.get('current_time', 'unknown')
        }
        
        return json.dumps(export_data, indent=2)
    
    def import_customization(self, json_data: str) -> Optional[Dict[str, Any]]:
        """Import customization settings from JSON"""
        
        try:
            data = json.loads(json_data)
            return data.get('settings', {})
            
        except Exception as e:
            st.error(f"Failed to import customization: {str(e)}")
            return None