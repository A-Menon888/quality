import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from data_extractor import ProcessData
from scipy import stats

class ProcessCapabilityGenerator:
    """Advanced Process Capability Analysis Generator"""
    
    def __init__(self):
        self.colors = {
            'process': '#1f77b4',
            'spec_limits': '#ff7f0e',
            'target': '#2ca02c',
            'capability_zone': '#d62728'
        }
        self.chart_style = {
            'figure_size': (14, 10),
            'dpi': 100,
            'facecolor': 'white'
        }
    
    def generate_capability_analysis(self, process_data: ProcessData,
                                   show_histogram: bool = True,
                                   show_control_limits: bool = True,
                                   show_capability_zone: bool = True) -> Dict[str, Any]:
        """Generate comprehensive process capability analysis"""
        
        if not process_data or len(process_data.measurements) < 30:
            raise ValueError("Insufficient process data for capability analysis (minimum 30 data points required)")
        
        if not process_data.specifications:
            raise ValueError("Specification limits required for capability analysis")
        
        measurements = process_data.measurements
        specs = process_data.specifications
        
        # Calculate basic statistics
        mean_val = np.mean(measurements)
        std_val = np.std(measurements, ddof=1)
        
        # Get specification limits
        usl = specs.get('usl')
        lsl = specs.get('lsl')
        target = specs.get('target', (usl + lsl) / 2 if usl and lsl else mean_val)
        
        if not usl or not lsl:
            raise ValueError("Both USL and LSL must be provided for capability analysis")
        
        # Calculate capability indices
        tolerance = usl - lsl
        cp = tolerance / (6 * std_val)  # Process capability
        cpu = (usl - mean_val) / (3 * std_val)  # Upper capability
        cpl = (mean_val - lsl) / (3 * std_val)  # Lower capability
        cpk = min(cpu, cpl)  # Process capability index
        
        # Calculate sigma level
        sigma_level = cpk * 3
        
        # Calculate defect rate (assuming normal distribution)
        z_usl = (usl - mean_val) / std_val
        z_lsl = (lsl - mean_val) / std_val
        defect_rate_upper = 1 - stats.norm.cdf(z_usl)
        defect_rate_lower = stats.norm.cdf(z_lsl)
        total_defect_rate = defect_rate_upper + defect_rate_lower
        ppm = total_defect_rate * 1_000_000
        
        # Create the figure
        fig = plt.figure(figsize=self.chart_style['figure_size'])
        
        if show_histogram:
            # Create subplot layout
            gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], width_ratios=[3, 1])
            ax_main = fig.add_subplot(gs[0, 0])
            ax_hist = fig.add_subplot(gs[1, 0])
            ax_stats = fig.add_subplot(gs[:, 1])
        else:
            gs = fig.add_gridspec(1, 2, width_ratios=[3, 1])
            ax_main = fig.add_subplot(gs[0, 0])
            ax_stats = fig.add_subplot(gs[0, 1])
            ax_hist = None
        
        # Main histogram with normal curve
        n, bins_edges, patches = ax_main.hist(measurements, bins='auto', alpha=0.7, 
                                            color=self.colors['process'], edgecolor='black', linewidth=0.5)
        
        # Add normal distribution curve
        x_range = np.linspace(min(measurements), max(measurements), 100)
        normal_curve = stats.norm.pdf(x_range, mean_val, std_val) * len(measurements) * (bins_edges[1] - bins_edges[0])
        ax_main.plot(x_range, normal_curve, color='red', linewidth=3, 
                    label=f'Normal Distribution (μ={mean_val:.3f}, σ={std_val:.3f})')
        
        # Add specification limits
        ax_main.axvline(x=usl, color=self.colors['spec_limits'], linestyle='-', 
                       linewidth=3, label=f'USL={usl:.3f}')
        ax_main.axvline(x=lsl, color=self.colors['spec_limits'], linestyle='-', 
                       linewidth=3, label=f'LSL={lsl:.3f}')
        
        # Add target line
        ax_main.axvline(x=target, color=self.colors['target'], linestyle='--', 
                       linewidth=2, label=f'Target={target:.3f}')
        
        # Add mean line
        ax_main.axvline(x=mean_val, color='purple', linestyle=':', 
                       linewidth=2, label=f'Mean={mean_val:.3f}')
        
        # Add capability zone if requested
        if show_capability_zone:
            # Shade the area within specification limits
            x_fill = np.linspace(lsl, usl, 100)
            y_fill = stats.norm.pdf(x_fill, mean_val, std_val) * len(measurements) * (bins_edges[1] - bins_edges[0])
            ax_main.fill_between(x_fill, 0, y_fill, alpha=0.3, color='green', 
                               label='Within Spec Limits')
        
        # Customize main chart
        ax_main.set_xlabel('Measurement Value', fontsize=12, fontweight='bold')
        ax_main.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax_main.set_title('Process Capability Analysis', fontsize=14, fontweight='bold', pad=20)
        ax_main.legend(loc='upper right')
        ax_main.grid(True, alpha=0.3)
        
        # Add histogram in bottom panel if requested
        if show_histogram and ax_hist:
            ax_hist.hist(measurements, bins='auto', alpha=0.7, color=self.colors['process'], 
                        edgecolor='black', linewidth=0.5)
            ax_hist.axvline(x=usl, color=self.colors['spec_limits'], linestyle='-', linewidth=2)
            ax_hist.axvline(x=lsl, color=self.colors['spec_limits'], linestyle='-', linewidth=2)
            ax_hist.axvline(x=mean_val, color='purple', linestyle=':', linewidth=2)
            ax_hist.set_xlabel('Measurement Value', fontsize=10, fontweight='bold')
            ax_hist.set_ylabel('Count', fontsize=10, fontweight='bold')
            ax_hist.grid(True, alpha=0.3)
        
        # Add statistics panel
        stats_text = f'''Process Capability Analysis
        
Basic Statistics:
Sample Size: {len(measurements)}
Mean (μ): {mean_val:.4f}
Std Dev (σ): {std_val:.4f}
Target: {target:.4f}

Specification Limits:
USL: {usl:.4f}
LSL: {lsl:.4f}
Tolerance: {tolerance:.4f}

Capability Indices:
Cp: {cp:.3f}
Cpu: {cpu:.3f}
Cpl: {cpl:.3f}
Cpk: {cpk:.3f}

Sigma Level: {sigma_level:.2f}σ

Quality Metrics:
Defect Rate: {total_defect_rate:.6f}
PPM: {ppm:.0f}

Capability Assessment:
{"✓ Process is capable" if cpk >= 1.33 else "✗ Process needs improvement"}
{"✓ Meets 6σ target" if sigma_level >= 6 else "✗ Below 6σ target"}'''
        
        ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes, 
                     fontsize=10, verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        ax_stats.axis('off')
        
        plt.tight_layout()
        
        # Convert to bytes
        import io
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.chart_style['dpi'], 
                   bbox_inches='tight', facecolor=self.chart_style['facecolor'])
        buffer.seek(0)
        chart_bytes = buffer.getvalue()
        plt.close(fig)
        
        # Calculate comprehensive statistics
        statistics = {
            'sample_size': len(measurements),
            'mean': mean_val,
            'std_dev': std_val,
            'target': target,
            'usl': usl,
            'lsl': lsl,
            'tolerance': tolerance,
            'cp': cp,
            'cpu': cpu,
            'cpl': cpl,
            'cpk': cpk,
            'sigma_level': sigma_level,
            'defect_rate': total_defect_rate,
            'ppm': ppm,
            'is_capable': cpk >= 1.33,
            'meets_6sigma': sigma_level >= 6,
            'capability_grade': self._get_capability_grade(cpk)
        }
        
        # Enhanced metadata for AI analysis
        chart_metadata = {
            'chart_type': 'process_capability',
            'capability_indices': {
                'cp': cp,
                'cpu': cpu,
                'cpl': cpl,
                'cpk': cpk
            },
            'specification_limits': {
                'usl': usl,
                'lsl': lsl,
                'target': target,
                'tolerance': tolerance
            },
            'process_performance': {
                'sigma_level': sigma_level,
                'defect_rate': total_defect_rate,
                'ppm': ppm,
                'capability_grade': self._get_capability_grade(cpk)
            },
            'process_center': mean_val,
            'process_spread': std_val,
            'capability_assessment': 'capable' if cpk >= 1.33 else 'marginal' if cpk >= 1.0 else 'incapable',
            'six_sigma_status': 'achieved' if sigma_level >= 6 else 'not_achieved',
            'process_name': getattr(process_data, 'process_name', None),
            'data_source': getattr(process_data, 'source', 'unknown'),
            'improvement_priority': 'high' if cpk < 1.0 else 'medium' if cpk < 1.33 else 'low'
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'chart_metadata': chart_metadata,
            'measurements': measurements
        }
    
    def generate_capability_control_chart(self, process_data: ProcessData,
                                        subgroup_size: int = 5) -> Dict[str, Any]:
        """Generate control chart with capability analysis overlay"""
        
        if not process_data or len(process_data.measurements) < 20:
            raise ValueError("Insufficient process data for capability control chart")
        
        measurements = process_data.measurements
        specs = process_data.specifications
        
        if not specs or 'usl' not in specs or 'lsl' not in specs:
            raise ValueError("Specification limits required for capability control chart")
        
        usl = specs['usl']
        lsl = specs['lsl']
        target = specs.get('target', (usl + lsl) / 2)
        
        # Create subgroups
        subgroups = []
        for i in range(0, len(measurements), subgroup_size):
            subgroup = measurements[i:i + subgroup_size]
            if len(subgroup) == subgroup_size:
                subgroups.append(subgroup)
        
        subgroup_means = [np.mean(subgroup) for subgroup in subgroups]
        subgroup_ranges = [np.max(subgroup) - np.min(subgroup) for subgroup in subgroups]
        
        # Calculate control limits
        grand_mean = np.mean(subgroup_means)
        mean_range = np.mean(subgroup_ranges)
        
        # Control chart constants
        constants = self._get_control_chart_constants(subgroup_size)
        A2 = constants['A2']
        
        ucl_xbar = grand_mean + A2 * mean_range
        lcl_xbar = grand_mean - A2 * mean_range
        
        # Create the figure
        fig, ax = plt.subplots(figsize=self.chart_style['figure_size'])
        
        # Plot subgroup means
        x_values = range(1, len(subgroup_means) + 1)
        ax.plot(x_values, subgroup_means, 'o-', color=self.colors['process'], 
               linewidth=2, markersize=6, label='Subgroup Means')
        
        # Add control limits
        ax.axhline(y=grand_mean, color='green', linestyle='-', linewidth=2, 
                  label=f'Center Line (μ={grand_mean:.3f})')
        ax.axhline(y=ucl_xbar, color='red', linestyle='--', linewidth=2, 
                  label=f'UCL={ucl_xbar:.3f}')
        ax.axhline(y=lcl_xbar, color='red', linestyle='--', linewidth=2, 
                  label=f'LCL={lcl_xbar:.3f}')
        
        # Add specification limits
        ax.axhline(y=usl, color=self.colors['spec_limits'], linestyle='-', 
                  linewidth=3, label=f'USL={usl:.3f}')
        ax.axhline(y=lsl, color=self.colors['spec_limits'], linestyle='-', 
                  linewidth=3, label=f'LSL={lsl:.3f}')
        ax.axhline(y=target, color=self.colors['target'], linestyle=':', 
                  linewidth=2, label=f'Target={target:.3f}')
        
        # Highlight out-of-control points
        out_of_control = [(i+1, val) for i, val in enumerate(subgroup_means) 
                         if val > ucl_xbar or val < lcl_xbar]
        if out_of_control:
            out_x, out_y = zip(*out_of_control)
            ax.scatter(out_x, out_y, color='red', s=100, zorder=5, 
                      label=f'Out of Control ({len(out_of_control)} points)')
        
        # Customize the chart
        ax.set_xlabel('Subgroup Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Subgroup Mean', fontsize=12, fontweight='bold')
        ax.set_title('Process Capability Control Chart', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
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
            'ucl_xbar': ucl_xbar,
            'lcl_xbar': lcl_xbar,
            'usl': usl,
            'lsl': lsl,
            'target': target,
            'out_of_control_points': len(out_of_control),
            'process_capable': len(out_of_control) == 0
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'subgroup_means': subgroup_means
        }
    
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
        return constants.get(subgroup_size, constants[5])
    
    def _get_capability_grade(self, cpk: float) -> str:
        """Get capability grade based on Cpk value"""
        if cpk >= 1.67:
            return "A+ (Excellent)"
        elif cpk >= 1.33:
            return "A (Good)"
        elif cpk >= 1.0:
            return "B (Marginal)"
        elif cpk >= 0.67:
            return "C (Poor)"
        else:
            return "D (Unacceptable)"
    
    def generate_capability_summary_table(self, process_data: ProcessData) -> pd.DataFrame:
        """Generate a detailed capability analysis summary table"""
        
        if not process_data or not process_data.specifications:
            return pd.DataFrame()
        
        measurements = process_data.measurements
        specs = process_data.specifications
        
        usl = specs.get('usl')
        lsl = specs.get('lsl')
        target = specs.get('target', (usl + lsl) / 2 if usl and lsl else np.mean(measurements))
        
        if not usl or not lsl:
            return pd.DataFrame()
        
        # Calculate all capability metrics
        mean_val = np.mean(measurements)
        std_val = np.std(measurements, ddof=1)
        tolerance = usl - lsl
        
        cp = tolerance / (6 * std_val)
        cpu = (usl - mean_val) / (3 * std_val)
        cpl = (mean_val - lsl) / (3 * std_val)
        cpk = min(cpu, cpl)
        
        # Create summary table
        summary_data = {
            'Metric': [
                'Sample Size', 'Mean', 'Std Dev', 'Target', 'USL', 'LSL', 'Tolerance',
                'Cp', 'Cpu', 'Cpl', 'Cpk', 'Sigma Level', 'Capability Grade'
            ],
            'Value': [
                len(measurements), f"{mean_val:.4f}", f"{std_val:.4f}", f"{target:.4f}",
                f"{usl:.4f}", f"{lsl:.4f}", f"{tolerance:.4f}",
                f"{cp:.3f}", f"{cpu:.3f}", f"{cpl:.3f}", f"{cpk:.3f}",
                f"{cpk * 3:.2f}σ", self._get_capability_grade(cpk)
            ],
            'Target': [
                '≥30', '=Target', 'Minimize', 'Specified', 'Specified', 'Specified', 'Fixed',
                '≥1.33', '≥1.33', '≥1.33', '≥1.33', '≥6.0', 'A or better'
            ]
        }
        
        return pd.DataFrame(summary_data)