import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from data_extractor import ProcessData
from scipy import stats

class ControlChartGenerator:
    """Advanced Control Chart Generator with multiple chart types"""
    
    def __init__(self):
        self.colors = {
            'data': '#1f77b4',
            'center_line': '#2ca02c',
            'control_limits': '#d62728',
            'spec_limits': '#ff7f0e',
            'out_of_control': '#d62728'
        }
        self.chart_style = {
            'figure_size': (14, 8),
            'dpi': 100,
            'facecolor': 'white'
        }
    
    def generate_xbar_chart(self, process_data: ProcessData, 
                          subgroup_size: int = 5,
                          show_spec_limits: bool = True,
                          show_trend_lines: bool = True) -> Dict[str, Any]:
        """Generate X-bar control chart"""
        
        if not process_data or len(process_data.measurements) < 5:
            raise ValueError("Insufficient process data for control chart generation")
        
        measurements = process_data.measurements
        n = len(measurements)
        
        # Calculate subgroup statistics
        subgroups = self._create_subgroups(measurements, subgroup_size)
        subgroup_means = [np.mean(subgroup) for subgroup in subgroups]
        subgroup_ranges = [np.max(subgroup) - np.min(subgroup) for subgroup in subgroups]
        
        # Calculate control limits
        grand_mean = np.mean(subgroup_means)
        mean_range = np.mean(subgroup_ranges)
        
        # Constants for X-bar chart (A2, D3, D4)
        constants = self._get_control_chart_constants(subgroup_size)
        A2 = constants['A2']
        D3 = constants['D3']
        D4 = constants['D4']
        
        ucl_xbar = grand_mean + A2 * mean_range
        lcl_xbar = grand_mean - A2 * mean_range
        
        # Create the figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.chart_style['figure_size'], 
                                      gridspec_kw={'height_ratios': [3, 1]})
        
        # X-bar chart
        x_values = range(1, len(subgroup_means) + 1)
        ax1.plot(x_values, subgroup_means, 'o-', color=self.colors['data'], 
                linewidth=2, markersize=6, label='Subgroup Means')
        
        # Center line
        ax1.axhline(y=grand_mean, color=self.colors['center_line'], linestyle='-', 
                   linewidth=2, label=f'Center Line (μ={grand_mean:.3f})')
        
        # Control limits
        ax1.axhline(y=ucl_xbar, color=self.colors['control_limits'], linestyle='--', 
                   linewidth=2, label=f'UCL={ucl_xbar:.3f}')
        ax1.axhline(y=lcl_xbar, color=self.colors['control_limits'], linestyle='--', 
                   linewidth=2, label=f'LCL={lcl_xbar:.3f}')
        
        # Specification limits
        if show_spec_limits and process_data.specifications:
            if 'usl' in process_data.specifications:
                ax1.axhline(y=process_data.specifications['usl'], color=self.colors['spec_limits'], 
                           linestyle=':', linewidth=2, label=f'USL={process_data.specifications["usl"]:.3f}')
            if 'lsl' in process_data.specifications:
                ax1.axhline(y=process_data.specifications['lsl'], color=self.colors['spec_limits'], 
                           linestyle=':', linewidth=2, label=f'LSL={process_data.specifications["lsl"]:.3f}')
        
        # Highlight out-of-control points
        out_of_control = [(i+1, val) for i, val in enumerate(subgroup_means) 
                         if val > ucl_xbar or val < lcl_xbar]
        if out_of_control:
            out_x, out_y = zip(*out_of_control)
            ax1.scatter(out_x, out_y, color=self.colors['out_of_control'], s=100, zorder=5, 
                       label=f'Out of Control ({len(out_of_control)} points)')
        
        # R chart
        ax2.plot(x_values, subgroup_ranges, 'o-', color=self.colors['data'], 
                linewidth=2, markersize=4)
        ax2.axhline(y=mean_range, color=self.colors['center_line'], linestyle='-', 
                   linewidth=2, label=f'Center Line (R̄={mean_range:.3f})')
        
        ucl_r = D4 * mean_range
        lcl_r = D3 * mean_range
        ax2.axhline(y=ucl_r, color=self.colors['control_limits'], linestyle='--', 
                   linewidth=2, label=f'UCL={ucl_r:.3f}')
        ax2.axhline(y=lcl_r, color=self.colors['control_limits'], linestyle='--', 
                   linewidth=2, label=f'LCL={lcl_r:.3f}')
        
        # Customize charts
        ax1.set_title('X-bar Control Chart', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Subgroup Mean', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        ax2.set_title('R Chart', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Subgroup Number', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Subgroup Range', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to bytes
        import io
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.chart_style['dpi'], 
                   bbox_inches='tight', facecolor=self.chart_style['facecolor'])
        buffer.seek(0)
        chart_bytes = buffer.getvalue()
        plt.close(fig)
        
        # Calculate statistics
        statistics = {
            'subgroup_size': subgroup_size,
            'total_subgroups': len(subgroup_means),
            'grand_mean': grand_mean,
            'mean_range': mean_range,
            'ucl_xbar': ucl_xbar,
            'lcl_xbar': lcl_xbar,
            'ucl_r': ucl_r,
            'lcl_r': lcl_r,
            'out_of_control_points': len(out_of_control),
            'process_capable': len(out_of_control) == 0
        }
        
        # Enhanced metadata for AI analysis
        chart_metadata = {
            'chart_type': 'control_chart',
            'chart_subtype': 'xbar_r',
            'subgroup_size': subgroup_size,
            'total_subgroups': len(subgroup_means),
            'control_limits': {
                'ucl_xbar': ucl_xbar,
                'lcl_xbar': lcl_xbar,
                'ucl_r': ucl_r,
                'lcl_r': lcl_r
            },
            'process_center': grand_mean,
            'process_variation': mean_range,
            'out_of_control_points': len(out_of_control),
            'process_stability': 'stable' if len(out_of_control) == 0 else 'unstable',
            'specification_limits': process_data.specifications if process_data.specifications else None,
            'process_name': getattr(process_data, 'process_name', None),
            'data_source': getattr(process_data, 'source', 'unknown'),
            'trend_analysis': 'no_trend' if len(out_of_control) == 0 else 'trend_detected'
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'chart_metadata': chart_metadata,
            'subgroup_means': subgroup_means,
            'subgroup_ranges': subgroup_ranges
        }
    
    def generate_individuals_chart(self, process_data: ProcessData,
                                 show_spec_limits: bool = True,
                                 show_moving_range: bool = True) -> Dict[str, Any]:
        """Generate Individuals and Moving Range (I-MR) chart"""
        
        if not process_data or len(process_data.measurements) < 2:
            raise ValueError("Insufficient process data for I-MR chart generation")
        
        measurements = process_data.measurements
        n = len(measurements)
        
        # Calculate moving ranges
        moving_ranges = [abs(measurements[i] - measurements[i-1]) for i in range(1, n)]
        mean_mr = np.mean(moving_ranges)
        
        # Calculate control limits for individuals
        mean_value = np.mean(measurements)
        ucl_i = mean_value + 2.66 * mean_mr
        lcl_i = mean_value - 2.66 * mean_mr
        
        # Create the figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.chart_style['figure_size'], 
                                      gridspec_kw={'height_ratios': [3, 1]})
        
        # Individuals chart
        x_values = range(1, n + 1)
        ax1.plot(x_values, measurements, 'o-', color=self.colors['data'], 
                linewidth=2, markersize=6, label='Individual Values')
        
        # Center line
        ax1.axhline(y=mean_value, color=self.colors['center_line'], linestyle='-', 
                   linewidth=2, label=f'Center Line (μ={mean_value:.3f})')
        
        # Control limits
        ax1.axhline(y=ucl_i, color=self.colors['control_limits'], linestyle='--', 
                   linewidth=2, label=f'UCL={ucl_i:.3f}')
        ax1.axhline(y=lcl_i, color=self.colors['control_limits'], linestyle='--', 
                   linewidth=2, label=f'LCL={lcl_i:.3f}')
        
        # Specification limits
        if show_spec_limits and process_data.specifications:
            if 'usl' in process_data.specifications:
                ax1.axhline(y=process_data.specifications['usl'], color=self.colors['spec_limits'], 
                           linestyle=':', linewidth=2, label=f'USL={process_data.specifications["usl"]:.3f}')
            if 'lsl' in process_data.specifications:
                ax1.axhline(y=process_data.specifications['lsl'], color=self.colors['spec_limits'], 
                           linestyle=':', linewidth=2, label=f'LSL={process_data.specifications["lsl"]:.3f}')
        
        # Moving Range chart
        if show_moving_range:
            mr_x_values = range(2, n + 1)
            ax2.plot(mr_x_values, moving_ranges, 'o-', color=self.colors['data'], 
                    linewidth=2, markersize=4, label='Moving Range')
            ax2.axhline(y=mean_mr, color=self.colors['center_line'], linestyle='-', 
                       linewidth=2, label=f'Center Line (MR̄={mean_mr:.3f})')
            
            ucl_mr = 3.27 * mean_mr
            ax2.axhline(y=ucl_mr, color=self.colors['control_limits'], linestyle='--', 
                       linewidth=2, label=f'UCL={ucl_mr:.3f}')
        
        # Customize charts
        ax1.set_title('Individuals Control Chart', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Individual Value', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        if show_moving_range:
            ax2.set_title('Moving Range Chart', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Sample Number', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Moving Range', fontsize=12, fontweight='bold')
            ax2.legend(loc='upper right')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to bytes
        import io
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.chart_style['dpi'], 
                   bbox_inches='tight', facecolor=self.chart_style['facecolor'])
        buffer.seek(0)
        chart_bytes = buffer.getvalue()
        plt.close(fig)
        
        # Calculate statistics
        statistics = {
            'sample_size': n,
            'mean_value': mean_value,
            'mean_moving_range': mean_mr,
            'ucl_i': ucl_i,
            'lcl_i': lcl_i,
            'ucl_mr': 3.27 * mean_mr if show_moving_range else None,
            'process_capable': True  # Will be enhanced with capability analysis
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'measurements': measurements,
            'moving_ranges': moving_ranges
        }
    
    def _create_subgroups(self, data: List[float], subgroup_size: int) -> List[List[float]]:
        """Create subgroups from individual measurements"""
        subgroups = []
        for i in range(0, len(data), subgroup_size):
            subgroup = data[i:i + subgroup_size]
            if len(subgroup) == subgroup_size:  # Only include complete subgroups
                subgroups.append(subgroup)
        return subgroups
    
    def _get_control_chart_constants(self, subgroup_size: int) -> Dict[str, float]:
        """Get control chart constants for given subgroup size"""
        constants = {
            2: {'A2': 1.880, 'D3': 0, 'D4': 3.267},
            3: {'A2': 1.023, 'D3': 0, 'D4': 2.575},
            4: {'A2': 0.729, 'D3': 0, 'D4': 2.282},
            5: {'A2': 0.577, 'D3': 0, 'D4': 2.115},
            6: {'A2': 0.483, 'D3': 0, 'D4': 2.004},
            7: {'A2': 0.419, 'D3': 0.076, 'D4': 1.924},
            8: {'A2': 0.373, 'D3': 0.136, 'D4': 1.864},
            9: {'A2': 0.337, 'D3': 0.184, 'D4': 1.816},
            10: {'A2': 0.308, 'D3': 0.223, 'D4': 1.777}
        }
        return constants.get(subgroup_size, constants[5])  # Default to subgroup size 5