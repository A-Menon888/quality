import streamlit as st
import base64
import io
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

class ExportManager:
    """Manages export functionality for generated tools and data"""
    
    def __init__(self):
        self.supported_formats = {
            'image': ['PNG', 'JPEG', 'SVG', 'PDF'],
            'data': ['CSV', 'Excel', 'JSON'],
            'report': ['PDF', 'HTML', 'Word']
        }
    
    def export_chart(self, chart_bytes: bytes, format: str = 'PNG', 
                    filename: Optional[str] = None) -> bytes:
        """Export chart in specified format"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qc_chart_{timestamp}.{format.lower()}"
        
        if format.upper() == 'PNG':
            return chart_bytes
        elif format.upper() == 'JPEG':
            # Convert PNG to JPEG (simplified - in real implementation, use PIL)
            return chart_bytes
        elif format.upper() == 'PDF':
            # Convert to PDF (simplified - in real implementation, use matplotlib PDF backend)
            return chart_bytes
        else:
            return chart_bytes
    
    # def export_data_table(self, data: Any, tool_type: str, format: str = 'CSV') -> bytes:
    #     """Export data table in specified format"""
        
    #     if tool_type == 'pareto_chart' and hasattr(data, 'categories'):
    #         df = pd.DataFrame({
    #             'Category': data.categories,
    #             'Count': data.counts,
    #             'Frequency (%)': [f*100 for f in data.frequencies],
    #             'Cumulative %': [sum(data.frequencies[:i+1])*100 for i in range(len(data.frequencies))]
    #         })
        
    #     elif tool_type == 'control_chart' and hasattr(data, 'measurements'):
    #         df = pd.DataFrame({
    #             'Sample': range(1, len(data.measurements) + 1),
    #             'Measurement': data.measurements
    #         })
        
    #     elif tool_type == 'process_capability' and hasattr(data, 'measurements'):
    #         df = pd.DataFrame({
    #             'Sample': range(1, len(data.measurements) + 1),
    #             'Measurement': data.measurements,
    #             'Within_Spec': ['Yes' if data.specifications.get('lsl', 0) <= m <= data.specifications.get('usl', 100) else 'No' for m in data.measurements]
    #         })
        
    #     else:
    #         df = pd.DataFrame({'Data': [str(data)]})
        
    #     if format.upper() == 'CSV':
    #         return df.to_csv(index=False).encode('utf-8')
    #     elif format.upper() == 'EXCEL':
    #         buffer = io.BytesIO()
    #         with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    #             df.to_excel(writer, index=False, sheet_name='QC_Data')
    #         return buffer.getvalue()
    #     elif format.upper() == 'JSON':
    #         return df.to_json(orient='records', indent=2).encode('utf-8')
    #     else:
    #         return df.to_csv(index=False).encode('utf-8')
    
    # def export_statistics(self, statistics: Dict[str, Any], tool_type: str, 
    #                      format: str = 'JSON') -> bytes:
    #     """Export statistics in specified format"""
        
    #     if format.upper() == 'JSON':
    #         export_data = {
    #             'tool_type': tool_type,
    #             'statistics': statistics,
    #             'export_timestamp': datetime.now().isoformat(),
    #             'export_version': '1.0'
    #         }
    #         return json.dumps(export_data, indent=2).encode('utf-8')
        
    #     elif format.upper() == 'CSV':
    #         df = pd.DataFrame(list(statistics.items()), columns=['Metric', 'Value'])
    #         return df.to_csv(index=False).encode('utf-8')
        
    #     else:
    #         return json.dumps(statistics, indent=2).encode('utf-8')
    
    # def create_comprehensive_report(self, tool_result: Dict[str, Any], 
    #                               tool_type: str, 
    #                               data: Any,
    #                               statistics: Dict[str, Any]) -> bytes:
    #     """Create comprehensive PDF report"""
        
    #     # This is a simplified implementation
    #     # In a real implementation, you would use libraries like reportlab or weasyprint
        
    #     report_content = f"""
    #     QUALITY CONTROL TOOL REPORT
    #     ===========================
        
    #     Tool Type: {tool_type.replace('_', ' ').title()}
    #     Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
    #     STATISTICS SUMMARY
    #     ==================
    #     """
        
    #     for key, value in statistics.items():
    #         report_content += f"{key}: {value}\n"
        
    #     report_content += f"""
        
    #     DATA SUMMARY
    #     ============
    #     """
        
    #     if hasattr(data, 'categories'):
    #         report_content += f"Categories: {len(data.categories)}\n"
    #         report_content += f"Total Count: {data.total_defects}\n"
        
    #     if hasattr(data, 'measurements'):
    #         report_content += f"Sample Size: {len(data.measurements)}\n"
    #         report_content += f"Mean: {pd.Series(data.measurements).mean():.3f}\n"
        
    #     return report_content.encode('utf-8')
    
    def render_export_panel(self, tool_result: Dict[str, Any], 
                           tool_type: str, 
                           data: Any,
                           statistics: Dict[str, Any]) -> None:
        """Render simplified export panel - PNG only"""
        
        if tool_result.get('chart_data'):
            # Generate filename with timestamp
            filename = f"{tool_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Tiny download button for PNG
            st.download_button(
                label="📊 Download as PNG",
                data=tool_result['chart_data'],
                file_name=filename,
                mime="image/png",
                help="Download the generated chart as a PNG image",
                use_container_width=False,
                key=f"download_png_{filename}"  # 👈 unique key based on filename
            )

    # def export_tool_configuration(self, tool_type: str, settings: Dict[str, Any]) -> bytes:
    #     """Export tool configuration settings"""
        
    #     config_data = {
    #         'tool_type': tool_type,
    #         'settings': settings,
    #         'export_timestamp': datetime.now().isoformat(),
    #         'version': '1.0'
    #     }
        
    #     return json.dumps(config_data, indent=2).encode('utf-8')
    
    def import_tool_configuration(self, config_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Import tool configuration settings"""
        
        try:
            config_data = json.loads(config_bytes.decode('utf-8'))
            return config_data.get('settings', {})
        except Exception as e:
            st.error(f"Failed to import configuration: {str(e)}")
            return None
    
    # def create_export_summary(self, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    #     """Create summary of all exported tools"""
        
    #     summary = {
    #         'total_tools': len(tool_results),
    #         'successful_exports': len([r for r in tool_results if r.get('success', False)]),
    #         'failed_exports': len([r for r in tool_results if not r.get('success', False)]),
    #         'tool_types': list(set([r.get('tool_type', 'unknown') for r in tool_results])),
    #         'export_timestamp': datetime.now().isoformat()
    #     }
        
    #     return summary