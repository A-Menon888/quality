import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
from typing import List, Dict, Any, Tuple
from data_extractor import CauseEffectData

class FishboneDiagramGenerator:
    """Advanced Fishbone Diagram Generator with interactive features"""
    
    def __init__(self):
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        self.chart_style = {
            'figure_size': (16, 10),
            'dpi': 100,
            'facecolor': 'white'
        }
        self.main_categories = ['Man', 'Machine', 'Material', 'Method', 'Measurement', 'Environment']
    
    def generate_advanced_fishbone(self, cause_effect_data: CauseEffectData,
                                 show_sub_causes: bool = True,
                                 show_connections: bool = True,
                                 title: str = "Fishbone Diagram - Root Cause Analysis") -> Dict[str, Any]:
        """Generate an advanced Fishbone diagram with enhanced features"""
        
        if not cause_effect_data or len(cause_effect_data.main_categories) == 0:
            raise ValueError("No cause-effect data available for Fishbone diagram generation")
        
        # Create the figure
        fig, ax = plt.subplots(figsize=self.chart_style['figure_size'])
        
        # Main spine (horizontal line)
        spine_length = 10
        spine_y = 0.5
        spine_start = 0.1
        spine_end = spine_start + spine_length
        
        # Draw main spine
        ax.plot([spine_start, spine_end], [spine_y, spine_y], 'k-', linewidth=4, alpha=0.8)
        
        # Problem box at the right end
        problem_width = 0.8
        problem_height = 0.15
        problem_box = FancyBboxPatch((spine_end - problem_width/2, spine_y - problem_height/2), 
                                   problem_width, problem_height,
                                   boxstyle="round,pad=0.05", facecolor='lightcoral', 
                                   edgecolor='darkred', linewidth=2)
        ax.add_patch(problem_box)
        
        # Problem text (truncated if too long)
        problem_text = cause_effect_data.problem[:30] + "..." if len(cause_effect_data.problem) > 30 else cause_effect_data.problem
        ax.text(spine_end, spine_y, problem_text, ha='center', va='center', 
               fontweight='bold', fontsize=12, color='darkred')
        
        # Main categories positions
        category_positions = np.linspace(spine_start + 1, spine_end - 1, len(self.main_categories))
        
        # Draw main branches and categories
        branches_data = []
        for i, (category, pos) in enumerate(zip(self.main_categories, category_positions)):
            # Determine branch direction (alternating up/down)
            branch_y = spine_y + (0.4 if i % 2 == 0 else -0.4)
            
            # Draw main branch
            ax.plot([pos, pos], [spine_y, branch_y], 'k-', linewidth=3, alpha=0.8)
            
            # Add category label with background
            label_width = 0.3
            label_height = 0.08
            label_box = FancyBboxPatch((pos - label_width/2, branch_y + (0.05 if branch_y > spine_y else -0.13)), 
                                     label_width, label_height,
                                     boxstyle="round,pad=0.02", facecolor=self.colors[i % len(self.colors)], 
                                     edgecolor='black', linewidth=1, alpha=0.8)
            ax.add_patch(label_box)
            
            ax.text(pos, branch_y + (0.09 if branch_y > spine_y else -0.17), 
                   category, ha='center', va='center' if branch_y > spine_y else 'top',
                   fontweight='bold', fontsize=11, color='white')
            
            # Collect branch data for sub-causes
            branches_data.append({
                'category': category,
                'position': pos,
                'branch_y': branch_y,
                'sub_causes': cause_effect_data.sub_causes.get(category, [])
            })
        
        # Draw sub-causes if requested
        if show_sub_causes:
            for branch in branches_data:
                sub_causes = branch['sub_causes'][:4]  # Limit to 4 sub-causes per category
                for j, sub_cause in enumerate(sub_causes):
                    sub_y = branch['branch_y'] + (0.15 if branch['branch_y'] > spine_y else -0.15) + (j * 0.1)
                    
                    # Draw sub-branch
                    sub_branch_length = 0.4
                    ax.plot([branch['position'], branch['position'] + sub_branch_length], 
                           [sub_y, sub_y], 'k--', alpha=0.6, linewidth=2)
                    
                    # Add sub-cause text
                    sub_text = sub_cause[:20] + "..." if len(sub_cause) > 20 else sub_cause
                    ax.text(branch['position'] + sub_branch_length + 0.1, sub_y, sub_text, 
                           ha='left', va='center', fontsize=9, alpha=0.8,
                           bbox=dict(boxstyle='round,pad=0.02', facecolor='lightyellow', alpha=0.7))
        
        # Add connections between related causes if requested
        if show_connections and len(cause_effect_data.sub_causes) > 1:
            self._add_cause_connections(ax, branches_data)
        
        # Set axis properties
        ax.set_xlim(0, spine_end + 2)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Add title
        ax.text(spine_end/2, 0.95, title, ha='center', va='top', 
               fontsize=16, fontweight='bold', color='darkblue')
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], color='black', linewidth=3, label='Main Categories'),
            plt.Line2D([0], [0], color='black', linewidth=2, linestyle='--', label='Sub-Causes'),
            plt.Rectangle((0, 0), 1, 1, facecolor='lightcoral', label='Problem Statement')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
        
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
        total_sub_causes = sum(len(causes) for causes in cause_effect_data.sub_causes.values())
        statistics = {
            'problem': cause_effect_data.problem,
            'main_categories': len(cause_effect_data.main_categories),
            'total_sub_causes': total_sub_causes,
            'confidence': cause_effect_data.confidence,
            'categories_with_causes': len([cat for cat in cause_effect_data.sub_causes if cause_effect_data.sub_causes[cat]])
        }
        
        # Enhanced metadata for AI analysis
        chart_metadata = {
            'chart_type': 'fishbone_diagram',
            'problem_statement': cause_effect_data.problem,
            'main_categories': cause_effect_data.main_categories,
            'sub_causes_by_category': cause_effect_data.sub_causes,
            'total_sub_causes': total_sub_causes,
            'analysis_confidence': cause_effect_data.confidence,
            'categories_with_causes': len([cat for cat in cause_effect_data.sub_causes if cause_effect_data.sub_causes[cat]]),
            'analysis_completeness': 'complete' if len(cause_effect_data.main_categories) >= 4 else 'partial',
            'cause_diversity': 'high' if total_sub_causes >= 10 else 'medium' if total_sub_causes >= 5 else 'low',
            'data_source': getattr(cause_effect_data, 'source', 'unknown'),
            'root_cause_analysis_status': 'in_progress' if cause_effect_data.confidence < 0.8 else 'completed'
        }
        
        return {
            'chart_bytes': chart_bytes,
            'statistics': statistics,
            'chart_metadata': chart_metadata,
            'main_categories': cause_effect_data.main_categories,
            'sub_causes': cause_effect_data.sub_causes
        }
    
    def _add_cause_connections(self, ax, branches_data: List[Dict]) -> None:
        """Add connection lines between related causes"""
        # Simple implementation - can be enhanced with more sophisticated logic
        for i, branch1 in enumerate(branches_data):
            for j, branch2 in enumerate(branches_data[i+1:], i+1):
                if branch1['sub_causes'] and branch2['sub_causes']:
                    # Draw a subtle connection line
                    ax.plot([branch1['position'], branch2['position']], 
                           [branch1['branch_y'], branch2['branch_y']], 
                           'k:', alpha=0.3, linewidth=1)
    
    def generate_cause_analysis_table(self, cause_effect_data: CauseEffectData) -> Dict[str, Any]:
        """Generate a detailed cause analysis table"""
        
        analysis = {
            'problem_statement': cause_effect_data.problem,
            'main_categories': [],
            'total_causes': 0,
            'confidence_level': cause_effect_data.confidence
        }
        
        for category in self.main_categories:
            sub_causes = cause_effect_data.sub_causes.get(category, [])
            analysis['main_categories'].append({
                'category': category,
                'sub_causes': sub_causes,
                'cause_count': len(sub_causes)
            })
            analysis['total_causes'] += len(sub_causes)
        
        return analysis