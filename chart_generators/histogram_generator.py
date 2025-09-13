import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from data_extractor import ProcessData
from scipy import stats

class HistogramGenerator:
    """Advanced Histogram Generator with statistical analysis"""
    
    def __init__(self):
        self.colors = {
            'histogram': '#1f77b4',
            'normal_curve': '#ff7f0e',
            'mean_line': '#d62728',
            'spec_limits': '#2ca02c'
        }
        self.chart_style = {
            'figure_size': (12, 8),
            'dpi': 100,
            'facecolor': 'white'
        }
    
    def generate_advanced_histogram(self, process_data: ProcessData,
                                  bins: str = 'auto',
                                  show_normal_curve: bool = True,
                                  show_statistics: bool = True,
                                  show_spec_limits: bool = True,
                                  title: str = "Histogram - Process Distribution Analysis") -> Dict[str, Any]:
        """Generate an advanced histogram with statistical analysis"""
        
        if not process_data or len(process_data.measurements) < 5:
            raise ValueError("Insufficient process data for histogram generation")
        
        measurements = process_data.measurements
        n = len(measurements)
        
        # Calculate statistics
        mean_val = np.mean(measurements)
        std_val = np.std(measurements, ddof=1)
        median_val = np.median(measurements)
        mode_val = stats.mode(measurements, keepdims=True)[0][0] if len(set(measurements)) < len(measurements) else None
        
        # Create the figure
        fig, ax = plt.subplots(figsize=self.chart_style['figure_size'])
        
        # Create histogram
        n, bins_edges, patches = ax.hist(measurements, bins=bins, alpha=0.7, 
                                        color=self.colors['histogram'], edgecolor='black', linewidth=0.5)
        
        # Add normal curve if requested
        if show_normal_curve:
            x_range = np.linspace(min(measurements), max(measurements), 100)
            normal_curve = stats.norm.pdf(x_range, mean_val, std_val) * len(measurements) * (bins_edges[1] - bins_edges[0])
            ax.plot(x_range, normal_curve, color=self.colors['normal_curve'], 
                   linewidth=3, label=f'Normal Distribution (μ={mean_val:.2f}, σ={std_val:.2f})')
        
        # Add mean line
        ax.axvline(x=mean_val, color=self.colors['mean_line'], linestyle='--', 
                  linewidth=2, label=f'Mean (μ={mean_val:.2f})')
        
        # Add median line
        ax.axvline(x=median_val, color='purple', linestyle=':', 
                  linewidth=2, label=f'Median (M={median_val:.2f})')
        
        # Add specification limits if available
        if show_spec_limits and process_data.specifications:
            if 'usl' in process_data.specifications:
                ax.axvline(x=process_data.specifications['usl'], color=self.colors['spec_limits'], 
                          linestyle='-', linewidth=2, label=f'USL={process_data.specifications["usl"]:.2f}')
            if 'lsl' in process_data.specifications:
                ax.axvline(x=process_data.specifications['lsl'], color=self.colors['spec_limits'], 
                          linestyle='-', linewidth=2, label=f'LSL={process_data.specifications["lsl"]:.2f}')
            if 'target' in process_data.specifications:
                ax.axvline(x=process_data.specifications['target'], color='orange', 
                          linestyle='-.', linewidth=2, label=f'Target={process_data.specifications["target"]:.2f}')
        
        # Customize the chart
        ax.set_xlabel('Measurement Value', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Add statistics text box
        if show_statistics:
            stats_text = f'''Statistics:
Sample Size: {len(measurements)}
Mean: {mean_val:.3f}
Std Dev: {std_val:.3f}
Median: {median_val:.3f}
Min: {min(measurements):.3f}
Max: {max(measurements):.3f}
Range: {max(measurements) - min(measurements):.3f}'''
            
            if mode_val is not None:
                stats_text += f'\nMode: {mode_val:.3f}'
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        # Convert to bytes
        import io
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.chart_style['dpi'], 
                   bbox_inches='tight', facecolor=self.chart_style['facecolor'])
        buffer.seek(0)
        chart_bytes = buffer.getvalue()
        plt.close(fig)
        
        # Calculate additional statistics
        skewness = stats.skew(measurements)
        kurtosis = stats.kurtosis(measurements)
        
        # Normality test
        shapiro_stat, shapiro_p = stats.shapiro(measurements) if len(measurements) <= 5000 else (None, None)
        
        statistics = {
            'sample_size': len(measurements),
            'mean': mean_val,
            'std_dev': std_val,
            'median': median_val,
            'mode': mode_val,
            'min': min(measurements),
            'max': max(measurements),
            'range': max(measurements) - min(measurements),
            'skewness': skewness,
            'kurtosis': kurtosis,
            'shapiro_stat': shapiro_stat,
            'shapiro_p': shapiro_p,
            'is_normal': shapiro_p > 0.05 if shapiro_p is not None else None
        }
        
        # Enhanced metadata for AI analysis
        chart_metadata = {
            'chart_type': 'histogram',
            'bin_count': len(bins_edges) - 1,
            'bin_width': (bins_edges[1] - bins_edges[0]) if len(bins_edges) > 1 else 0,
            'data_range': [min(measurements), max(measurements)],
            'distribution_shape': 'normal' if shapiro_p and shapiro_p > 0.05 else 'non-normal',
            'outliers_detected': len([x for x in measurements if abs(x - mean_val) > 3 * std_val]) > 0,
            'specification_limits': process_data.specifications if process_data.specifications else None,
            'process_name': getattr(process_data, 'process_name', None),
            'data_source': getattr(process_data, 'source', 'unknown')
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'chart_metadata': chart_metadata,
            'measurements': measurements,
            'bins': bins_edges
        }
    
    def generate_distribution_comparison(self, process_data: ProcessData) -> Dict[str, Any]:
        """Generate comparison with different theoretical distributions"""
        
        if not process_data or len(process_data.measurements) < 10:
            raise ValueError("Insufficient process data for distribution comparison")
        
        measurements = process_data.measurements
        
        # Create the figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Histogram with multiple distribution fits
        n, bins_edges, patches = ax1.hist(measurements, bins='auto', alpha=0.7, 
                                        color=self.colors['histogram'], edgecolor='black', linewidth=0.5)
        
        # Fit different distributions
        x_range = np.linspace(min(measurements), max(measurements), 100)
        
        # Normal distribution
        mean_val, std_val = stats.norm.fit(measurements)
        normal_curve = stats.norm.pdf(x_range, mean_val, std_val) * len(measurements) * (bins_edges[1] - bins_edges[0])
        ax1.plot(x_range, normal_curve, color='red', linewidth=2, label='Normal')
        
        # Log-normal distribution
        try:
            lognorm_params = stats.lognorm.fit(measurements)
            lognorm_curve = stats.lognorm.pdf(x_range, *lognorm_params) * len(measurements) * (bins_edges[1] - bins_edges[0])
            ax1.plot(x_range, lognorm_curve, color='green', linewidth=2, label='Log-Normal')
        except:
            pass
        
        # Weibull distribution
        try:
            weibull_params = stats.weibull_min.fit(measurements)
            weibull_curve = stats.weibull_min.pdf(x_range, *weibull_params) * len(measurements) * (bins_edges[1] - bins_edges[0])
            ax1.plot(x_range, weibull_curve, color='blue', linewidth=2, label='Weibull')
        except:
            pass
        
        ax1.set_title('Distribution Comparison', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Measurement Value', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Q-Q plot
        stats.probplot(measurements, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normal Distribution)', fontsize=14, fontweight='bold')
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
        
        return {
            'chart_bytes': chart_bytes,
            'measurements': measurements
        }