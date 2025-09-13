import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import io
import base64
from data_extractor import DefectData, ProcessData, CauseEffectData, QualityMetrics

@dataclass
class ToolGenerationResult:
    """Result of dynamic tool generation"""
    success: bool
    tool_type: str
    chart_data: Optional[bytes] = None
    chart_html: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None
    chart_metadata: Optional[Dict[str, Any]] = None
    error_message: str = ""

class BaseToolGenerator:
    """Base class for all QC tool generators"""
    
    def __init__(self):
        self.chart_style = {
            'figure_size': (10, 6),
            'dpi': 100,
            'facecolor': 'white',
            'edgecolor': 'black',
            'linewidth': 0.5
        }
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    def generate_chart_bytes(self, fig) -> bytes:
        """Convert matplotlib figure to bytes"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.chart_style['dpi'], 
                   bbox_inches='tight', facecolor=self.chart_style['facecolor'])
        buffer.seek(0)
        return buffer.getvalue()
    
    def create_data_summary(self, data: Any) -> Dict[str, Any]:
        """Create a summary of the data used for the chart"""
        return {"data_points": 0, "summary": "No data summary available"}

# ---------------- Pareto Chart ----------------
class ParetoChartGenerator(BaseToolGenerator):
    """Generates Pareto charts from defect data"""
    
    def generate(self, defect_data: DefectData) -> ToolGenerationResult:
        try:
            if not defect_data or len(defect_data.categories) == 0:
                return ToolGenerationResult(
                    success=False,
                    tool_type="Pareto Chart",
                    error_message="No defect data available for Pareto chart generation"
                )
            
            sorted_data = sorted(zip(defect_data.categories, defect_data.counts, defect_data.frequencies), 
                               key=lambda x: x[1], reverse=True)
            categories, counts, frequencies = zip(*sorted_data)
            cumulative_freq = np.cumsum(frequencies) * 100
            
            fig, ax1 = plt.subplots(figsize=self.chart_style['figure_size'])
            bars = ax1.bar(range(len(categories)), counts, color=self.colors[0], alpha=0.7)
            ax2 = ax1.twinx()
            ax2.plot(range(len(categories)), cumulative_freq, color='red', marker='o', linewidth=2, markersize=6)
            ax2.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='80% Line')
            
            ax1.set_xlabel('Defect Categories', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold', color=self.colors[0])
            ax2.set_ylabel('Cumulative Percentage (%)', fontsize=12, fontweight='bold', color='red')
            ax1.set_title('Pareto Chart - Defect Analysis', fontsize=14, fontweight='bold', pad=20)
            ax1.set_xticks(range(len(categories)))
            ax1.set_xticklabels(categories, rotation=45, ha='right')
            
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{count}', ha='center', va='bottom', fontweight='bold')
            
            for x, y in zip(range(len(categories)), cumulative_freq):
                ax2.text(x, y + 2, f'{y:.1f}%', ha='center', va='bottom', fontweight='bold', color='red')
            
            ax2.legend(loc='lower right')
            ax1.grid(True, alpha=0.3)
            plt.tight_layout()
            
            chart_bytes = self.generate_chart_bytes(fig)
            plt.close(fig)
            
            data_summary = {
                "total_defects": defect_data.total_defects,
                "categories": len(defect_data.categories),
                "top_category": categories[0] if categories else "N/A",
                "top_category_percentage": frequencies[0] * 100 if frequencies else 0,
                "pareto_80_percent": len([f for f in cumulative_freq if f <= 80])
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
                'pareto_effectiveness': 'high' if len([f for f in cumulative_freq if f <= 80]) <= 3 else 'medium' if len([f for f in cumulative_freq if f <= 80]) <= 5 else 'low'
            }
            
            return ToolGenerationResult(True, "Pareto Chart", chart_data=chart_bytes, data_summary=data_summary, chart_metadata=chart_metadata)
        except Exception as e:
            return ToolGenerationResult(False, "Pareto Chart", error_message=f"Error generating Pareto chart: {str(e)}")

# ---------------- Fishbone Diagram ----------------
class FishboneDiagramGenerator(BaseToolGenerator):
    """Generates Fishbone diagrams from cause-effect data"""
    
    def generate(self, cause_effect_data: CauseEffectData) -> ToolGenerationResult:
        try:
            if not cause_effect_data or len(cause_effect_data.main_categories) == 0:
                return ToolGenerationResult(False, "Fishbone Diagram", error_message="No cause-effect data available")
            
            fig, ax = plt.subplots(figsize=(12, 8))
            spine_length = 8
            spine_y = 0.5
            ax.plot([0.1, 0.1 + spine_length], [spine_y, spine_y], 'k-', linewidth=3)
            
            problem_box = FancyBboxPatch((0.1 + spine_length - 0.3, spine_y - 0.1), 0.6, 0.2,
                                       boxstyle="round,pad=0.02", facecolor='lightcoral', edgecolor='black', linewidth=2)
            ax.add_patch(problem_box)
            ax.text(0.1 + spine_length, spine_y, cause_effect_data.problem[:20] + "...", ha='center', va='center', fontweight='bold', fontsize=10)
            
            main_categories = ['Man', 'Machine', 'Material', 'Method', 'Measurement', 'Environment']
            category_positions = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]
            for i, (category, pos) in enumerate(zip(main_categories, category_positions)):
                branch_y = spine_y + (0.3 if i % 2 == 0 else -0.3)
                ax.plot([0.1 + pos, 0.1 + pos], [spine_y, branch_y], 'k-', linewidth=2)
                ax.text(0.1 + pos, branch_y + (0.05 if branch_y > spine_y else -0.05), category,
                        ha='center', va='center' if branch_y > spine_y else 'top', fontweight='bold', fontsize=11,
                        color=self.colors[i % len(self.colors)])
                if category in cause_effect_data.sub_causes:
                    sub_causes = cause_effect_data.sub_causes[category]
                    for j, sub_cause in enumerate(sub_causes[:3]):
                        sub_y = branch_y + (0.1 if branch_y > spine_y else -0.1) + (j * 0.08)
                        ax.plot([0.1 + pos, 0.1 + pos + 0.3], [sub_y, sub_y], 'k--', alpha=0.7)
                        ax.text(0.1 + pos + 0.35, sub_y, sub_cause[:15] + "...", ha='left', va='center', fontsize=9, alpha=0.8)
            
            ax.set_xlim(0, 1.5)
            ax.set_ylim(0, 1)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.text(0.75, 0.95, 'Fishbone Diagram - Root Cause Analysis', ha='center', va='top', fontsize=14, fontweight='bold')
            plt.tight_layout()
            chart_bytes = self.generate_chart_bytes(fig)
            plt.close(fig)
            
            data_summary = {
                "problem": cause_effect_data.problem,
                "main_categories": len(cause_effect_data.main_categories),
                "total_sub_causes": sum(len(causes) for causes in cause_effect_data.sub_causes.values()),
                "confidence": cause_effect_data.confidence
            }
            return ToolGenerationResult(True, "Fishbone Diagram", chart_data=chart_bytes, data_summary=data_summary)
        except Exception as e:
            return ToolGenerationResult(False, "Fishbone Diagram", error_message=f"Error generating Fishbone diagram: {str(e)}")

# ---------------- Control Chart ----------------
class ControlChartGenerator(BaseToolGenerator):
    """Generates control charts from process data"""
    
    def generate(self, process_data: ProcessData) -> ToolGenerationResult:
        try:
            if not process_data or len(process_data.measurements) < 5:
                return ToolGenerationResult(False, "Control Chart", error_message="Insufficient process data")
            
            measurements = process_data.measurements
            n = len(measurements)
            mean = np.mean(measurements)
            std = np.std(measurements, ddof=1)
            ucl = mean + 3 * std
            lcl = mean - 3 * std
            
            fig, ax = plt.subplots(figsize=self.chart_style['figure_size'])
            x_values = range(1, n + 1)
            ax.plot(x_values, measurements, 'o-', color=self.colors[0], linewidth=2, markersize=6)
            ax.axhline(y=mean, color='green', linestyle='-', linewidth=2, label=f'Center Line (μ={mean:.2f})')
            ax.axhline(y=ucl, color='red', linestyle='--', linewidth=2, label=f'UCL={ucl:.2f}')
            ax.axhline(y=lcl, color='red', linestyle='--', linewidth=2, label=f'LCL={lcl:.2f}')
            
            if process_data.specifications:
                if 'usl' in process_data.specifications:
                    ax.axhline(y=process_data.specifications['usl'], color='orange', linestyle=':', linewidth=2, label=f'USL={process_data.specifications["usl"]:.2f}')
                if 'lsl' in process_data.specifications:
                    ax.axhline(y=process_data.specifications['lsl'], color='orange', linestyle=':', linewidth=2, label=f'LSL={process_data.specifications["lsl"]:.2f}')
            
            out_of_control = [(i+1, val) for i, val in enumerate(measurements) if val > ucl or val < lcl]
            if out_of_control:
                out_x, out_y = zip(*out_of_control)
                ax.scatter(out_x, out_y, color='red', s=100, zorder=5, label=f'Out of Control ({len(out_of_control)} points)')
            
            ax.set_xlabel('Sample Number', fontsize=12, fontweight='bold')
            ax.set_ylabel('Measurement Value', fontsize=12, fontweight='bold')
            ax.set_title('Control Chart (X-bar)', fontsize=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            chart_bytes = self.generate_chart_bytes(fig)
            plt.close(fig)
            
            data_summary = {
                "sample_size": n,
                "mean": mean,
                "std_dev": std,
                "ucl": ucl,
                "lcl": lcl,
                "out_of_control_points": len(out_of_control),
                "process_capable": len(out_of_control) == 0
            }
            return ToolGenerationResult(True, "Control Chart", chart_data=chart_bytes, data_summary=data_summary)
        except Exception as e:
            return ToolGenerationResult(False, "Control Chart", error_message=f"Error generating control chart: {str(e)}")

# ---------------- Histogram ----------------
class HistogramGenerator(BaseToolGenerator):
    """Generates histogram from process data"""
    
    def generate(self, process_data: ProcessData) -> ToolGenerationResult:
        try:
            if not process_data or len(process_data.measurements) < 5:
                return ToolGenerationResult(False, "Histogram", error_message="Insufficient data for histogram")
            
            measurements = process_data.measurements
            fig, ax = plt.subplots(figsize=self.chart_style['figure_size'])
            ax.hist(measurements, bins='auto', color=self.colors[0], alpha=0.7, edgecolor='black')
            ax.set_xlabel('Measurement Value', fontsize=12, fontweight='bold')
            ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
            ax.set_title('Histogram - Process Data Distribution', fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            chart_bytes = self.generate_chart_bytes(fig)
            plt.close(fig)
            
            data_summary = {
                "sample_size": len(measurements),
                "mean": np.mean(measurements),
                "std_dev": np.std(measurements, ddof=1),
                "min": np.min(measurements),
                "max": np.max(measurements)
            }
            return ToolGenerationResult(True, "Histogram", chart_data=chart_bytes, data_summary=data_summary)
        except Exception as e:
            return ToolGenerationResult(False, "Histogram", error_message=f"Error generating histogram: {str(e)}")

# ---------------- Process Capability Chart ----------------
class CapabilityChartGenerator(BaseToolGenerator):
    """Generates process capability chart (histogram + Cp/Cpk)"""
    
    def generate(self, process_data: ProcessData) -> ToolGenerationResult:
        try:
            if not process_data or len(process_data.measurements) < 5:
                return ToolGenerationResult(False, "Capability Chart", error_message="Insufficient data")
            
            measurements = np.array(process_data.measurements)
            mean = np.mean(measurements)
            std = np.std(measurements, ddof=1)
            usl = process_data.specifications.get('usl') if process_data.specifications else None
            lsl = process_data.specifications.get('lsl') if process_data.specifications else None
            
            fig, ax = plt.subplots(figsize=self.chart_style['figure_size'])
            ax.hist(measurements, bins='auto', color=self.colors[0], alpha=0.7, edgecolor='black', density=True)
            x = np.linspace(min(measurements), max(measurements), 100)
            ax.plot(x, 1/(std*np.sqrt(2*np.pi))*np.exp(-0.5*((x-mean)/std)**2), 'r-', linewidth=2)
            
            if usl is not None:
                ax.axvline(usl, color='orange', linestyle='--', linewidth=2, label=f'USL={usl}')
            if lsl is not None:
                ax.axvline(lsl, color='orange', linestyle='--', linewidth=2, label=f'LSL={lsl}')
            
            ax.set_xlabel('Measurement Value', fontsize=12, fontweight='bold')
            ax.set_ylabel('Density', fontsize=12, fontweight='bold')
            ax.set_title('Process Capability Chart', fontsize=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            chart_bytes = self.generate_chart_bytes(fig)
            plt.close(fig)
            
            Cp = Cpk = None
            if usl is not None and lsl is not None:
                Cp = (usl - lsl) / (6 * std)
                Cpk = min((usl - mean) / (3 * std), (mean - lsl) / (3 * std))
            
            data_summary = {
                "sample_size": len(measurements),
                "mean": mean,
                "std_dev": std,
                "usl": usl,
                "lsl": lsl,
                "Cp": Cp,
                "Cpk": Cpk
            }
            return ToolGenerationResult(True, "Capability Chart", chart_data=chart_bytes, data_summary=data_summary)
        except Exception as e:
            return ToolGenerationResult(False, "Capability Chart", error_message=f"Error generating capability chart: {str(e)}")

class DynamicToolGenerator:
    """Main class for generating QC tools dynamically"""
    
    def __init__(self):
        self.generators = {
            'pareto_chart': ParetoChartGenerator(),
            'fishbone_diagram': FishboneDiagramGenerator(),
            'control_chart': ControlChartGenerator(),
            'histogram': HistogramGenerator(),
            'capability_chart': CapabilityChartGenerator()
        }
    
    def generate_tool(self, tool_type: str, data: Any) -> ToolGenerationResult:
        """Generate a specific QC tool based on tool type and data"""
        try:
            if tool_type not in self.generators:
                return ToolGenerationResult(
                    success=False,
                    tool_type=tool_type,
                    error_message=f"Tool generator not available for {tool_type}"
                )
            
            generator = self.generators[tool_type]
            return generator.generate(data)
            
        except Exception as e:
            return ToolGenerationResult(
                success=False,
                tool_type=tool_type,
                error_message=f"Error generating {tool_type}: {str(e)}"
            )
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool generators"""
        return list(self.generators.keys())
    
    def get_tool_requirements(self, tool_type: str) -> Dict[str, Any]:
        """Get requirements for a specific tool type"""
        requirements = {
            'pareto_chart': {
                'required_data': 'DefectData',
                'min_data_points': 3,
                'description': 'Requires defect categories and their frequencies'
            },
            'fishbone_diagram': {
                'required_data': 'CauseEffectData', 
                'min_data_points': 2,
                'description': 'Requires problem statement and cause categories'
            },
            'control_chart': {
                'required_data': 'ProcessData',
                'min_data_points': 5,
                'description': 'Requires process measurements over time'
            },
            'histogram': {
                'required_data': 'ProcessData',
                'min_data_points': 5,
                'description': 'Requires process data values for frequency distribution'
            },
            'capability_chart': {
                'required_data': 'ProcessData',
                'min_data_points': 10,
                'description': 'Requires process data with specification limits for Cp/Cpk analysis'
            }
        }
        return requirements.get(tool_type, {})
