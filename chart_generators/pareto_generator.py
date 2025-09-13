import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from data_extractor import DefectData

class ParetoChartGenerator:
    """Advanced Pareto Chart Generator with enhanced features"""
    
    def __init__(self):
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        self.chart_style = {
            'figure_size': (12, 8),
            'dpi': 100,
            'facecolor': 'white'
        }
    
    def generate_advanced_pareto(self, defect_data: DefectData, 
                               show_80_20_line: bool = True,
                               show_cumulative_percentage: bool = True,
                               show_value_labels: bool = True,
                               title: str = "Pareto Chart - Defect Analysis") -> Dict[str, Any]:
        """Generate an advanced Pareto chart with customizable features"""
        
        if not defect_data or len(defect_data.categories) == 0:
            raise ValueError("No defect data available for Pareto chart generation")
        
        # Sort data by frequency (descending)
        sorted_data = sorted(zip(defect_data.categories, defect_data.counts, defect_data.frequencies), 
                           key=lambda x: x[1], reverse=True)
        
        categories, counts, frequencies = zip(*sorted_data)
        
        # Calculate cumulative percentages
        cumulative_freq = np.cumsum(frequencies) * 100
        
        # Create the figure and axis
        fig, ax1 = plt.subplots(figsize=self.chart_style['figure_size'])
        
        # Create bar chart with gradient colors
        bars = []
        for i, (category, count) in enumerate(zip(categories, counts)):
            color = self.colors[i % len(self.colors)]
            bar = ax1.bar(i, count, color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
            bars.append(bar[0])
        
        # Create line chart for cumulative percentage
        ax2 = ax1.twinx()
        line = ax2.plot(range(len(categories)), cumulative_freq, 
                      color='red', marker='o', linewidth=3, markersize=8, 
                      markerfacecolor='white', markeredgecolor='red', markeredgewidth=2)
        
        # Add 80% line if requested
        if show_80_20_line:
            ax2.axhline(y=80, color='red', linestyle='--', alpha=0.7, linewidth=2, 
                       label='80% Pareto Line')
        
        # Customize the chart
        ax1.set_xlabel('Defect Categories', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Frequency', fontsize=14, fontweight='bold', color='#1f77b4')
        ax2.set_ylabel('Cumulative Percentage (%)', fontsize=14, fontweight='bold', color='red')
        
        ax1.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax1.set_xticks(range(len(categories)))
        ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=12)
        
        # Add value labels on bars if requested
        if show_value_labels:
            for i, (bar, count, freq) in enumerate(zip(bars, counts, frequencies)):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                        f'{count}\n({freq*100:.1f}%)', ha='center', va='bottom', 
                        fontweight='bold', fontsize=10)
        
        # Add percentage labels on line if requested
        if show_cumulative_percentage:
            for i, (x, y) in enumerate(zip(range(len(categories)), cumulative_freq)):
                ax2.text(x, y + 2, f'{y:.1f}%', ha='center', va='bottom', 
                        fontweight='bold', color='red', fontsize=11)
        
        # Add legend
        if show_80_20_line:
            ax2.legend(loc='lower right', fontsize=12)
        
        # Add grid
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add summary statistics
        pareto_80_count = len([f for f in cumulative_freq if f <= 80])
        ax1.text(0.02, 0.98, f'Total Defects: {defect_data.total_defects}\n'
                             f'Categories: {len(categories)}\n'
                             f'80% Rule: {pareto_80_count} categories', 
                transform=ax1.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
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
            'total_defects': defect_data.total_defects,
            'categories': len(categories),
            'top_category': categories[0],
            'top_category_count': counts[0],
            'top_category_percentage': frequencies[0] * 100,
            'pareto_80_categories': pareto_80_count,
            'pareto_80_percentage': cumulative_freq[pareto_80_count-1] if pareto_80_count > 0 else 0
        }
        
        # Enhanced metadata for AI analysis
        chart_metadata = {
            'chart_type': 'pareto_chart',
            'defect_categories': categories,
            'defect_counts': counts,
            'defect_frequencies': [f * 100 for f in frequencies],
            'cumulative_frequencies': cumulative_freq.tolist(),
            'pareto_80_rule_applied': True,
            'top_3_categories': categories[:3] if len(categories) >= 3 else categories,
            'top_3_percentage': sum(frequencies[:3]) * 100 if len(frequencies) >= 3 else sum(frequencies) * 100,
            'time_period': getattr(defect_data, 'time_period', None),
            'data_source': getattr(defect_data, 'source', 'unknown'),
            'pareto_effectiveness': 'high' if pareto_80_count <= 3 else 'medium' if pareto_80_count <= 5 else 'low'
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'chart_metadata': chart_metadata,
            'categories': categories,
            'counts': counts,
            'frequencies': frequencies,
            'cumulative_frequencies': cumulative_freq
        }
    
    def generate_pareto_table(self, defect_data: DefectData) -> pd.DataFrame:
        """Generate a detailed Pareto analysis table"""
        
        if not defect_data or len(defect_data.categories) == 0:
            return pd.DataFrame()
        
        # Sort data by frequency (descending)
        sorted_data = sorted(zip(defect_data.categories, defect_data.counts, defect_data.frequencies), 
                           key=lambda x: x[1], reverse=True)
        
        categories, counts, frequencies = zip(*sorted_data)
        cumulative_freq = np.cumsum(frequencies) * 100
        
        # Create DataFrame
        df = pd.DataFrame({
            'Category': categories,
            'Count': counts,
            'Frequency (%)': [f*100 for f in frequencies],
            'Cumulative Frequency (%)': cumulative_freq,
            'Pareto Classification': ['A' if f <= 80 else 'B' if f <= 95 else 'C' for f in cumulative_freq]
        })
        
        return df