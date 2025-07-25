"""
Centralized subplot management system for stock chart technical indicators.

This module provides the SubplotManager class that handles intelligent layout
calculation, conflict resolution, and extensible subplot configuration for
technical indicators like RSI, MACD, Volume, and Time Selector.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass
class SubplotConfiguration:
    """Configuration for a single subplot type."""
    name: str
    height_ratio: float
    title: str
    show_grid: bool
    y_axis_title: str
    priority: int
    conflicts_with: List[str]
    requires: List[str]


@dataclass
class ValidationResult:
    """Result of subplot combination validation."""
    valid: bool
    conflicts: List[Dict[str, Any]]
    suggestions: List[str]
    max_subplots_exceeded: bool
    alternative_configs: List[Dict[str, Any]]


@dataclass
class LayoutResult:
    """Result of layout calculation."""
    subplot_rows: Dict[str, int]
    height_ratios: List[float]
    total_rows: int
    price_chart_domain: Tuple[float, float]
    conflicts_resolved: List[str]
    warnings: List[str]


class SubplotError(Exception):
    """Custom exception for subplot-related errors."""
    def __init__(self, message: str, conflicts: List[str] = None, suggestions: List[str] = None):
        super().__init__(message)
        self.conflicts = conflicts or []
        self.suggestions = suggestions or []


class SubplotManager:
    """
    Centralized manager for stock chart subplots and technical indicators.
    
    This class handles layout calculation, conflict resolution, and provides
    a clean API for coordinating between frontend settings and backend
    subplot creation.
    """
    
    def __init__(self):
        """Initialize the SubplotManager with default configurations."""
        self.subplot_configs = {
            'volume': SubplotConfiguration(
                name='volume',
                height_ratio=0.2,
                title='Volume',
                show_grid=False,
                y_axis_title='Volume',
                priority=1,
                conflicts_with=[],
                requires=[]
            ),
            'rsi': SubplotConfiguration(
                name='rsi',
                height_ratio=0.2,
                title='RSI',
                show_grid=False,
                y_axis_title='RSI (0-100)',
                priority=2,
                conflicts_with=[],
                requires=[]
            ),
            'macd': SubplotConfiguration(
                name='macd',
                height_ratio=0.25,
                title='MACD',
                show_grid=False,
                y_axis_title='MACD',
                priority=3,
                conflicts_with=[],
                requires=[]
            ),
            'time_selector': SubplotConfiguration(
                name='time_selector',
                height_ratio=0.15,
                title='',
                show_grid=False,
                y_axis_title='',
                priority=4,
                conflicts_with=['rsi', 'macd', 'volume'],
                requires=[]
            )
        }
        
        # Configuration constraints
        self.max_subplots = 3  # Reasonable limit for readability
        self.min_price_height = 0.4  # Minimum height for price chart
    
    def validate_subplot_combination(self, requested_subplots: List[str]) -> ValidationResult:
        """
        Validate that requested subplot combination is feasible.
        
        This method performs comprehensive validation including:
        - Unknown subplot detection
        - Direct conflict detection between subplots
        - Maximum subplot limit enforcement
        - Missing requirement validation
        - Layout feasibility checks
        
        Args:
            requested_subplots: List of subplot names to include
            
        Returns:
            ValidationResult: Validation result with conflicts and suggestions
        """
        conflicts = []
        suggestions = []
        alternative_configs = []
        
        # Remove duplicates while preserving order
        requested_subplots = list(dict.fromkeys(requested_subplots))
        
        # Check if all requested subplots exist
        unknown_subplots = [sp for sp in requested_subplots if sp not in self.subplot_configs]
        if unknown_subplots:
            conflicts.append({
                'type': 'unknown_subplot',
                'subplots': unknown_subplots,
                'message': f"Unknown subplot types: {', '.join(unknown_subplots)}. Available types: {', '.join(self.get_available_subplots())}"
            })
        
        # Filter to only known subplots for further validation
        valid_subplots = [sp for sp in requested_subplots if sp in self.subplot_configs]
        
        # Check for missing requirements
        missing_requirements = self._check_missing_requirements(valid_subplots)
        if missing_requirements:
            for subplot, missing in missing_requirements.items():
                conflicts.append({
                    'type': 'missing_requirements',
                    'subplot': subplot,
                    'missing': missing,
                    'message': f"'{subplot}' requires the following subplots to be enabled: {', '.join(missing)}"
                })
        
        # Check for direct conflicts between subplots
        direct_conflicts = self._detect_direct_conflicts(valid_subplots)
        conflicts.extend(direct_conflicts)
        
        # Check maximum subplot limit
        max_exceeded = len(valid_subplots) > self.max_subplots
        if max_exceeded:
            conflicts.append({
                'type': 'max_subplots_exceeded',
                'requested': len(valid_subplots),
                'maximum': self.max_subplots,
                'message': f"Too many subplots requested ({len(valid_subplots)}). Maximum allowed: {self.max_subplots}. Consider prioritizing the most important indicators."
            })
        
        # Check if layout would be feasible (price chart height)
        layout_issues = self._check_layout_feasibility(valid_subplots)
        if layout_issues:
            conflicts.extend(layout_issues)
        
        # Generate suggestions for conflict resolution
        if conflicts:
            suggestions = self._generate_conflict_suggestions(valid_subplots, conflicts)
            alternative_configs = self._generate_alternative_configs(valid_subplots, conflicts)
        else:
            alternative_configs = []
        
        return ValidationResult(
            valid=len(conflicts) == 0,
            conflicts=conflicts,
            suggestions=suggestions,
            max_subplots_exceeded=max_exceeded,
            alternative_configs=alternative_configs
        )
    
    def _check_missing_requirements(self, valid_subplots: List[str]) -> Dict[str, List[str]]:
        """
        Check if any subplots have missing requirements.
        
        Args:
            valid_subplots: List of valid subplot names
            
        Returns:
            Dict mapping subplot names to their missing requirements
        """
        missing_requirements = {}
        
        for subplot in valid_subplots:
            config = self.subplot_configs[subplot]
            missing = [req for req in config.requires if req not in valid_subplots]
            if missing:
                missing_requirements[subplot] = missing
        
        return missing_requirements
    
    def _detect_direct_conflicts(self, valid_subplots: List[str]) -> List[Dict[str, Any]]:
        """
        Detect direct conflicts between subplots.
        
        Args:
            valid_subplots: List of valid subplot names
            
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        for subplot_name in valid_subplots:
            config = self.subplot_configs[subplot_name]
            conflicting = [sp for sp in valid_subplots if sp in config.conflicts_with]
            if conflicting:
                conflicts.append({
                    'type': 'direct_conflict',
                    'subplot': subplot_name,
                    'conflicts_with': conflicting,
                    'message': f"'{subplot_name}' cannot be used together with: {', '.join(conflicting)}. These indicators are incompatible due to layout constraints."
                })
        
        return conflicts
    
    def _check_layout_feasibility(self, valid_subplots: List[str]) -> List[Dict[str, Any]]:
        """
        Check if the requested subplot combination would create a feasible layout.
        
        Args:
            valid_subplots: List of valid subplot names
            
        Returns:
            List of layout issue dictionaries
        """
        layout_issues = []
        
        if not valid_subplots:
            return layout_issues
        
        # Calculate what the scaled heights would be
        total_subplot_height = sum(self.subplot_configs[sp].height_ratio for sp in valid_subplots)
        
        # Only flag as an issue if scaling would make subplots unreadably small
        if total_subplot_height > (1.0 - self.min_price_height):
            available_height = 1.0 - self.min_price_height
            scale_factor = available_height / total_subplot_height
            
            # Check if any subplot would become too small after scaling
            min_readable_height = 0.05  # 5% minimum for readability (more lenient)
            for subplot in valid_subplots:
                scaled_height = self.subplot_configs[subplot].height_ratio * scale_factor
                if scaled_height < min_readable_height:
                    layout_issues.append({
                        'type': 'subplot_too_small',
                        'subplot': subplot,
                        'scaled_height': scaled_height,
                        'min_height': min_readable_height,
                        'message': f"'{subplot}' would be scaled to {scaled_height:.1%} height, which is too small for readability (minimum: {min_readable_height:.1%}). Consider using fewer subplots."
                    })
        
        return layout_issues
    
    def _generate_conflict_suggestions(self, requested_subplots: List[str], conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate helpful suggestions for resolving conflicts."""
        suggestions = []
        
        for conflict in conflicts:
            if conflict['type'] == 'direct_conflict':
                subplot = conflict['subplot']
                conflicting = conflict['conflicts_with']
                # Suggest removing the lower priority subplot
                subplot_priority = self.subplot_configs[subplot].priority
                conflicting_priorities = [(sp, self.subplot_configs[sp].priority) for sp in conflicting]
                lowest_priority = max(conflicting_priorities + [(subplot, subplot_priority)], key=lambda x: x[1])
                suggestions.append(f"Remove '{lowest_priority[0]}' (lowest priority) to resolve conflict between '{subplot}' and {conflicting}")
            
            elif conflict['type'] == 'max_subplots_exceeded':
                # Suggest removing lowest priority subplots
                valid_subplots = [sp for sp in requested_subplots if sp in self.subplot_configs]
                sorted_subplots = sorted(valid_subplots, key=lambda x: self.subplot_configs[x].priority)
                to_keep = sorted_subplots[:self.max_subplots]
                to_remove = sorted_subplots[self.max_subplots:]
                suggestions.append(f"Keep highest priority subplots: {', '.join(to_keep)}. Remove: {', '.join(to_remove)}")
            
            elif conflict['type'] == 'missing_requirements':
                subplot = conflict['subplot']
                missing = conflict['missing']
                suggestions.append(f"Add required subplots for '{subplot}': {', '.join(missing)}")
            
            elif conflict['type'] == 'insufficient_price_height':
                suggestions.append("Reduce the number of subplots to ensure the price chart remains readable")
            
            elif conflict['type'] == 'subplot_too_small':
                subplot = conflict['subplot']
                suggestions.append(f"Remove '{subplot}' or other subplots to prevent it from becoming too small to read")
            
            elif conflict['type'] == 'unknown_subplot':
                unknown = conflict['subplots']
                available = self.get_available_subplots()
                suggestions.append(f"Replace unknown subplots {unknown} with available types: {', '.join(available)}")
        
        return suggestions
    
    def _generate_alternative_configs(self, requested_subplots: List[str], conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alternative configurations that would work based on detected conflicts."""
        alternatives = []
        valid_subplots = [sp for sp in requested_subplots if sp in self.subplot_configs]
        
        if not valid_subplots:
            return alternatives
        
        # Generate config with automatic conflict resolution
        resolved_subplots, _ = self._resolve_conflicts_automatically(requested_subplots)
        if resolved_subplots and resolved_subplots != valid_subplots:
            alternatives.append({
                'subplots': resolved_subplots,
                'description': 'Automatically resolved conflicts by priority',
                'priority': 1
            })
        
        # Generate config with only non-conflicting subplots
        non_conflicting = self._get_non_conflicting_subplots(valid_subplots)
        if non_conflicting and non_conflicting != resolved_subplots:
            # Validate that this configuration is actually feasible
            if self._is_combination_feasible(non_conflicting):
                alternatives.append({
                    'subplots': non_conflicting,
                    'description': 'Configuration with all conflicting subplots removed',
                    'priority': 2
                })
        
        # Generate config with highest priority subplots only (if max exceeded)
        has_max_exceeded = any(c['type'] == 'max_subplots_exceeded' for c in conflicts)
        if has_max_exceeded:
            sorted_by_priority = sorted(valid_subplots, key=lambda x: self.subplot_configs[x].priority)
            high_priority = sorted_by_priority[:self.max_subplots]
            if high_priority not in [alt['subplots'] for alt in alternatives]:
                # Validate that this configuration is actually feasible
                if self._is_combination_feasible(high_priority):
                    alternatives.append({
                        'subplots': high_priority,
                        'description': f'Top {self.max_subplots} highest priority subplots',
                        'priority': 3
                    })
        
        # Generate feasible combinations by systematically reducing subplots
        feasible_combinations = self._generate_feasible_combinations(valid_subplots)
        for combo in feasible_combinations:
            if combo not in [alt['subplots'] for alt in alternatives]:
                alternatives.append({
                    'subplots': combo,
                    'description': f'Feasible combination with {len(combo)} subplot(s)',
                    'priority': 6
                })
        
        # Generate minimal viable configs for specific conflict types
        for conflict in conflicts:
            if conflict['type'] == 'direct_conflict':
                # Create config without the conflicting subplot
                subplot = conflict['subplot']
                without_conflict = [sp for sp in valid_subplots if sp != subplot]
                if without_conflict and self._is_combination_feasible(without_conflict):
                    alternatives.append({
                        'subplots': without_conflict,
                        'description': f"Configuration without '{subplot}' to resolve conflicts",
                        'priority': 4
                    })
            
            elif conflict['type'] == 'insufficient_price_height':
                # Create config with fewer subplots to ensure readable price chart
                sorted_by_priority = sorted(valid_subplots, key=lambda x: self.subplot_configs[x].priority)
                for i in range(1, len(sorted_by_priority)):
                    subset = sorted_by_priority[:i]
                    if self._is_combination_feasible(subset):
                        alternatives.append({
                            'subplots': subset,
                            'description': f'Reduced to {i} subplot(s) for readable price chart',
                            'priority': 5
                        })
                        break
        
        # Remove duplicates and sort by priority
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            key = tuple(sorted(alt['subplots']))
            if key not in seen:
                seen.add(key)
                unique_alternatives.append(alt)
        
        # Sort by priority and remove priority field for output
        unique_alternatives.sort(key=lambda x: x.get('priority', 999))
        for alt in unique_alternatives:
            alt.pop('priority', None)
        
        return unique_alternatives[:5]  # Limit to top 5 alternatives
    
    def _get_non_conflicting_subplots(self, valid_subplots: List[str]) -> List[str]:
        """Get a list of subplots with no conflicts between them."""
        non_conflicting = []
        
        # Sort by priority to prefer higher priority subplots
        sorted_subplots = sorted(valid_subplots, key=lambda x: self.subplot_configs[x].priority)
        
        for subplot in sorted_subplots:
            config = self.subplot_configs[subplot]
            # Check if this subplot conflicts with any already selected
            has_conflict = any(sp in non_conflicting for sp in config.conflicts_with)
            # Also check if any selected subplot conflicts with this one
            conflicts_with_selected = any(
                subplot in self.subplot_configs[sp].conflicts_with 
                for sp in non_conflicting
            )
            
            if not has_conflict and not conflicts_with_selected:
                non_conflicting.append(subplot)
        
        return non_conflicting
    
    def _generate_feasible_combinations(self, valid_subplots: List[str]) -> List[List[str]]:
        """
        Generate feasible combinations of subplots by systematically testing combinations.
        
        Args:
            valid_subplots: List of valid subplot names
            
        Returns:
            List of feasible subplot combinations, sorted by preference
        """
        feasible_combinations = []
        
        # Sort by priority for consistent ordering
        sorted_subplots = sorted(valid_subplots, key=lambda x: self.subplot_configs[x].priority)
        
        # Try combinations of different sizes, starting with larger ones
        from itertools import combinations
        
        for size in range(min(len(sorted_subplots), self.max_subplots), 0, -1):
            for combo in combinations(sorted_subplots, size):
                combo_list = list(combo)
                # Use a simple validation check to avoid recursion
                if self._is_combination_feasible(combo_list):
                    feasible_combinations.append(combo_list)
                    
                    # Limit the number of combinations to avoid too many alternatives
                    if len(feasible_combinations) >= 3:
                        break
            
            # If we found feasible combinations of this size, we can stop
            # (prefer larger combinations)
            if feasible_combinations:
                break
        
        return feasible_combinations
    
    def _is_combination_feasible(self, subplots: List[str]) -> bool:
        """
        Simple feasibility check without generating alternatives (to avoid recursion).
        
        Args:
            subplots: List of subplot names to check
            
        Returns:
            bool: True if combination is feasible
        """
        # Check basic constraints without generating alternatives
        if len(subplots) > self.max_subplots:
            return False
        
        # Check for direct conflicts
        for subplot in subplots:
            if subplot not in self.subplot_configs:
                return False
            config = self.subplot_configs[subplot]
            if any(sp in subplots for sp in config.conflicts_with):
                return False
        
        # Check missing requirements
        for subplot in subplots:
            config = self.subplot_configs[subplot]
            if any(req not in subplots for req in config.requires):
                return False
        
        # Check layout feasibility - be more lenient, allow scaling
        total_subplot_height = sum(self.subplot_configs[sp].height_ratio for sp in subplots)
        
        # Only reject if scaling would make subplots unreadably small
        if total_subplot_height > (1.0 - self.min_price_height):
            available_height = 1.0 - self.min_price_height
            scale_factor = available_height / total_subplot_height
            min_readable_height = 0.05  # 5% minimum for readability (more lenient)
            
            for subplot in subplots:
                scaled_height = self.subplot_configs[subplot].height_ratio * scale_factor
                if scaled_height < min_readable_height:
                    return False
        
        return True
    
    def get_subplot_config(self, subplot_name: str) -> Optional[SubplotConfiguration]:
        """Get configuration for a specific subplot."""
        return self.subplot_configs.get(subplot_name)
    
    def get_available_subplots(self) -> List[str]:
        """Get list of all available subplot types."""
        return list(self.subplot_configs.keys())
    
    def add_subplot_config(self, config: SubplotConfiguration) -> None:
        """Add a new subplot configuration (for extensibility)."""
        self.subplot_configs[config.name] = config
    
    def remove_subplot_config(self, subplot_name: str) -> bool:
        """Remove a subplot configuration."""
        if subplot_name in self.subplot_configs:
            del self.subplot_configs[subplot_name]
            return True
        return False
    
    def calculate_layout(self, requested_subplots: List[str]) -> LayoutResult:
        """
        Calculate optimal subplot layout based on requested indicators.
        
        This method determines the optimal positioning and heights for all subplots
        while maintaining minimum price chart height and handling subplot priorities.
        
        Args:
            requested_subplots: List of subplot names to include
            
        Returns:
            LayoutResult: Layout configuration with rows, heights, and metadata
        """
        # First validate the subplot combination
        validation = self.validate_subplot_combination(requested_subplots)
        
        # If validation fails, resolve conflicts automatically
        conflicts_resolved = []
        warnings = []
        
        if not validation.valid:
            # Attempt automatic conflict resolution
            resolved_subplots, resolution_info = self._resolve_conflicts_automatically(requested_subplots)
            conflicts_resolved = resolution_info.get('resolved', [])
            warnings = resolution_info.get('warnings', [])
            requested_subplots = resolved_subplots
        
        # Filter to only valid, existing subplots
        valid_subplots = [sp for sp in requested_subplots if sp in self.subplot_configs]
        
        # Sort subplots by priority (lower number = higher priority)
        sorted_subplots = sorted(
            valid_subplots,
            key=lambda x: self.subplot_configs[x].priority
        )
        
        # Calculate row assignments
        subplot_rows = self._assign_subplot_rows(sorted_subplots)
        
        # Calculate height ratios with normalization
        height_ratios = self._calculate_height_ratios(sorted_subplots)
        
        # Calculate price chart domain based on subplot layout
        price_domain = self._calculate_price_chart_domain(height_ratios)
        
        return LayoutResult(
            subplot_rows=subplot_rows,
            height_ratios=height_ratios,
            total_rows=len(sorted_subplots) + 1,  # +1 for price chart
            price_chart_domain=price_domain,
            conflicts_resolved=conflicts_resolved,
            warnings=warnings
        )
    
    def _resolve_conflicts_automatically(self, requested_subplots: List[str]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Automatically resolve conflicts in subplot combinations.
        
        Args:
            requested_subplots: Original list of requested subplots
            
        Returns:
            Tuple of (resolved_subplots, resolution_info)
        """
        resolved_subplots = []
        resolution_info = {'resolved': [], 'warnings': []}
        
        # Filter out unknown subplots
        valid_subplots = [sp for sp in requested_subplots if sp in self.subplot_configs]
        unknown = [sp for sp in requested_subplots if sp not in self.subplot_configs]
        
        if unknown:
            resolution_info['warnings'].append(f"Removed unknown subplots: {', '.join(unknown)}")
        
        # Resolve direct conflicts by priority
        for subplot in sorted(valid_subplots, key=lambda x: self.subplot_configs[x].priority):
            config = self.subplot_configs[subplot]
            
            # Check if this subplot conflicts with any already resolved subplots
            has_conflict = any(sp in resolved_subplots for sp in config.conflicts_with)
            
            if not has_conflict:
                resolved_subplots.append(subplot)
            else:
                conflicting_with = [sp for sp in config.conflicts_with if sp in resolved_subplots]
                resolution_info['resolved'].append(
                    f"Removed '{subplot}' due to conflict with: {', '.join(conflicting_with)}"
                )
        
        # Enforce maximum subplot limit
        if len(resolved_subplots) > self.max_subplots:
            # Keep highest priority subplots
            original_count = len(resolved_subplots)
            resolved_subplots = resolved_subplots[:self.max_subplots]
            removed_count = original_count - len(resolved_subplots)
            resolution_info['warnings'].append(
                f"Removed {removed_count} lowest priority subplots to stay within limit of {self.max_subplots}"
            )
        
        return resolved_subplots, resolution_info
    
    def _assign_subplot_rows(self, sorted_subplots: List[str]) -> Dict[str, int]:
        """
        Assign row numbers to subplots based on priority.
        
        Args:
            sorted_subplots: List of subplot names sorted by priority
            
        Returns:
            Dict mapping subplot names to row numbers
        """
        subplot_rows = {'price': 1}  # Price chart always gets row 1
        
        # Assign subsequent rows to subplots in priority order
        for i, subplot_name in enumerate(sorted_subplots):
            subplot_rows[subplot_name] = i + 2  # Start from row 2
        
        return subplot_rows
    
    def _calculate_height_ratios(self, sorted_subplots: List[str]) -> List[float]:
        """
        Calculate height ratios for all chart rows with normalization.
        
        This method ensures the price chart maintains minimum height while
        distributing remaining space among subplots proportionally.
        
        Args:
            sorted_subplots: List of subplot names sorted by priority
            
        Returns:
            List of height ratios that sum to 1.0
        """
        if not sorted_subplots:
            # No subplots, price chart gets full height
            return [1.0]
        
        # Get base height ratios from configurations
        subplot_heights = [self.subplot_configs[sp].height_ratio for sp in sorted_subplots]
        total_subplot_height = sum(subplot_heights)
        
        # If subplots would make price chart too small, scale them down
        if total_subplot_height > (1.0 - self.min_price_height):
            available_height = 1.0 - self.min_price_height
            scale_factor = available_height / total_subplot_height
            subplot_heights = [h * scale_factor for h in subplot_heights]
            price_height = self.min_price_height
        else:
            # Normal case - price chart gets remaining space
            price_height = 1.0 - total_subplot_height
        
        # Combine price and subplot heights
        all_heights = [price_height] + subplot_heights
        
        # Normalize to ensure total equals 1.0 (handle floating point precision)
        total_height = sum(all_heights)
        if abs(total_height - 1.0) > 1e-10:  # Only normalize if significantly different
            all_heights = [h / total_height for h in all_heights]
        
        return all_heights
    
    def _calculate_price_chart_domain(self, height_ratios: List[float]) -> Tuple[float, float]:
        """
        Calculate the domain (y-axis range) for the price chart.
        
        Args:
            height_ratios: List of height ratios for all rows
            
        Returns:
            Tuple of (y_start, y_end) for price chart domain
        """
        if len(height_ratios) == 1:
            # Only price chart, use full domain
            return (0.0, 1.0)
        
        # Price chart is always the first row
        price_height = height_ratios[0]
        
        # Domain starts from the bottom of subplots and goes to top
        subplot_total_height = sum(height_ratios[1:])
        y_start = subplot_total_height
        y_end = 1.0
        
        return (y_start, y_end)
    
    def create_subplot_figure(self, requested_subplots: List[str], **kwargs) -> go.Figure:
        """
        Create Plotly figure with calculated subplot layout.
        
        This method uses the calculated layout to create a properly configured
        Plotly subplots figure with optimal spacing and title configuration.
        
        Args:
            requested_subplots: List of subplot names to include
            **kwargs: Additional configuration options:
                - vertical_spacing: Spacing between subplots (default: 0.05)
                - shared_xaxes: Whether to share x-axes (default: True)
                - subplot_titles: Custom titles for subplots (default: auto-generated)
                - figure_title: Main figure title (default: None)
        
        Returns:
            plotly.graph_objects.Figure: Configured subplot figure ready for data
        """
        # Calculate the optimal layout
        layout_result = self.calculate_layout(requested_subplots)
        
        # Extract configuration options from kwargs
        vertical_spacing = kwargs.get('vertical_spacing', 0.05)
        shared_xaxes = kwargs.get('shared_xaxes', True)
        custom_subplot_titles = kwargs.get('subplot_titles', None)
        figure_title = kwargs.get('figure_title', None)
        
        # Generate subplot titles based on configuration
        subplot_titles = self._generate_subplot_titles(
            requested_subplots, 
            layout_result, 
            custom_subplot_titles
        )
        
        # Create the subplot figure using Plotly's make_subplots
        fig = make_subplots(
            rows=layout_result.total_rows,
            cols=1,
            shared_xaxes=shared_xaxes,
            vertical_spacing=vertical_spacing,
            row_heights=layout_result.height_ratios,
            subplot_titles=subplot_titles,
            specs=self._generate_subplot_specs(layout_result.total_rows)
        )
        
        # Configure the figure layout for optimal display
        self._configure_figure_layout(fig, layout_result, figure_title)
        
        # Store layout metadata in the figure for later use
        fig._subplot_manager_metadata = {
            'layout_result': layout_result,
            'requested_subplots': requested_subplots,
            'subplot_rows': layout_result.subplot_rows
        }
        
        return fig
    
    def _generate_subplot_titles(self, requested_subplots: List[str], 
                                layout_result: LayoutResult, 
                                custom_titles: Optional[List[str]] = None) -> List[str]:
        """
        Generate appropriate titles for each subplot row.
        
        Args:
            requested_subplots: List of requested subplot names
            layout_result: Calculated layout result
            custom_titles: Optional custom titles to use instead
            
        Returns:
            List of titles for each subplot row
        """
        if custom_titles:
            # Ensure custom titles list matches the number of rows
            if len(custom_titles) == layout_result.total_rows:
                return custom_titles
            else:
                # Pad or truncate to match row count
                titles = custom_titles[:layout_result.total_rows]
                while len(titles) < layout_result.total_rows:
                    titles.append('')
                return titles
        
        # Auto-generate titles based on subplot configuration
        titles = []
        
        # Price chart title (always first row)
        titles.append('')  # Price chart typically doesn't need a title
        
        # Add titles for each requested subplot in row order
        sorted_subplots = sorted(
            [sp for sp in requested_subplots if sp in self.subplot_configs],
            key=lambda x: layout_result.subplot_rows.get(x, 999)
        )
        
        for subplot_name in sorted_subplots:
            config = self.subplot_configs[subplot_name]
            titles.append(config.title)
        
        return titles
    
    def _generate_subplot_specs(self, total_rows: int) -> List[List[Dict[str, Any]]]:
        """
        Generate subplot specifications for Plotly make_subplots.
        
        Args:
            total_rows: Total number of subplot rows
            
        Returns:
            List of subplot specifications
        """
        # Each row gets a single column with default secondary_y configuration
        specs = []
        for i in range(total_rows):
            specs.append([{"secondary_y": False}])
        
        return specs
    
    def _configure_figure_layout(self, fig: go.Figure, layout_result: LayoutResult, 
                                figure_title: Optional[str] = None) -> None:
        """
        Configure the figure layout for optimal display.
        
        Args:
            fig: Plotly figure to configure
            layout_result: Layout calculation result
            figure_title: Optional main figure title
        """
        # Set main figure title if provided
        #if figure_title:
        #    fig.update_layout(title=figure_title)
        
        # Configure overall layout properties
        fig.update_layout(
            showlegend=True,
            hovermode='x unified',
            dragmode='zoom',
            height=600,  # Default height, can be overridden
            margin=dict(l=50, r=50, t=50, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Configure x-axis properties for all subplots
        for i in range(1, layout_result.total_rows + 1):
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=1,
                linecolor='rgba(128,128,128,0.5)',
                row=i,
                col=1
            )
        
        # Configure y-axis properties for each subplot based on configuration
        self._configure_subplot_axes(fig, layout_result)
    
    def _configure_subplot_axes(self, fig: go.Figure, layout_result: LayoutResult) -> None:
        """
        Configure y-axis properties for each subplot based on their configuration.
        
        Args:
            fig: Plotly figure to configure
            layout_result: Layout calculation result
        """
        # Configure price chart y-axis (always row 1)
        fig.update_yaxes(
            title_text="Price ($)",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linewidth=1,
            linecolor='rgba(128,128,128,0.5)',
            row=1,
            col=1
        )
        
        # Configure y-axes for each subplot
        for subplot_name, row in layout_result.subplot_rows.items():
            if subplot_name == 'price':
                continue  # Already configured above
            
            if subplot_name in self.subplot_configs:
                config = self.subplot_configs[subplot_name]
                
                fig.update_yaxes(
                    title_text=config.y_axis_title,
                    showgrid=config.show_grid,
                    gridwidth=1 if config.show_grid else 0,
                    gridcolor='rgba(128,128,128,0.2)' if config.show_grid else None,
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(128,128,128,0.5)',
                    row=row,
                    col=1
                )
    
    def add_subplot_data(self, fig: go.Figure, subplot_name: str, data: Any, 
                        row: Optional[int] = None, **trace_kwargs) -> None:
        """
        Add data traces to specific subplot.
        
        This method provides a generic interface for adding data to subplots,
        with subplot-specific rendering handled by dedicated methods.
        
        Args:
            fig: Plotly figure object to add data to
            subplot_name: Name of subplot to add data to
            data: Data to plot (format depends on subplot type)
            row: Optional row number (auto-detected if not provided)
            **trace_kwargs: Additional trace configuration options
        """
        # Get subplot metadata from figure
        if not hasattr(fig, '_subplot_manager_metadata'):
            raise ValueError("Figure was not created by SubplotManager.create_subplot_figure()")
        
        metadata = fig._subplot_manager_metadata
        subplot_rows = metadata['subplot_rows']
        
        # Determine the row number
        if row is None:
            if subplot_name not in subplot_rows:
                raise ValueError(f"Subplot '{subplot_name}' not found in figure layout")
            row = subplot_rows[subplot_name]
        
        # Validate subplot configuration exists
        if subplot_name not in self.subplot_configs:
            raise ValueError(f"Unknown subplot type: '{subplot_name}'")
        
        # Route to appropriate subplot-specific method
        if subplot_name == 'volume':
            self._add_volume_data(fig, data, row, **trace_kwargs)
        elif subplot_name == 'rsi':
            self._add_rsi_data(fig, data, row, **trace_kwargs)
        elif subplot_name == 'macd':
            self._add_macd_data(fig, data, row, **trace_kwargs)
        elif subplot_name == 'time_selector':
            self._add_time_selector_data(fig, data, row, **trace_kwargs)
        else:
            # Generic fallback for custom subplot types
            self._add_generic_subplot_data(fig, subplot_name, data, row, **trace_kwargs)
    
    def _add_volume_data(self, fig: go.Figure, data: Any, row: int, **trace_kwargs) -> None:
        """
        Add volume bar chart data to subplot.
        
        Args:
            fig: Plotly figure object
            data: Volume data - can be pandas Series, dict with 'x' and 'y', or dict with 'dates' and 'volume'
            row: Row number for the subplot
            **trace_kwargs: Additional trace configuration options
        """
        try:
            # Handle different data formats
            if hasattr(data, 'index') and hasattr(data, 'values'):
                # Pandas Series-like data
                x_data = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in data.index]
                y_data = data.values.tolist()
            elif isinstance(data, dict):
                if 'x' in data and 'y' in data:
                    # Dictionary with x/y data
                    x_data = data['x']
                    y_data = data['y']
                elif 'dates' in data and 'volume' in data:
                    # Dictionary with dates/volume data
                    x_data = data['dates']
                    y_data = data['volume']
                else:
                    raise ValueError("Volume data dict must contain either 'x'/'y' or 'dates'/'volume' keys")
            else:
                raise ValueError("Volume data must be pandas Series or dict with appropriate keys")
            
            # Default trace configuration for volume bars
            default_config = {
                'name': 'Volume',
                'marker_color': 'rgba(158, 158, 158, 0.8)',
                'hovertemplate': '<b>Volume</b><br>Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>'
            }
            
            # Merge with user-provided kwargs
            trace_config = {**default_config, **trace_kwargs}
            
            # Add volume bar chart
            fig.add_trace(
                go.Bar(
                    x=x_data,
                    y=y_data,
                    **trace_config
                ),
                row=row,
                col=1
            )
            
        except Exception as e:
            print(f"Error adding volume data: {str(e)}")
            # Add empty trace to maintain subplot structure
            fig.add_trace(
                go.Bar(
                    x=[],
                    y=[],
                    name='Volume (Error)',
                    marker_color='rgba(255, 0, 0, 0.3)'
                ),
                row=row,
                col=1
            )
    
    def _add_rsi_data(self, fig: go.Figure, data: Any, row: int, **trace_kwargs) -> None:
        """
        Add RSI line chart data with overbought/oversold levels to subplot.
        
        Args:
            fig: Plotly figure object
            data: RSI data - can be pandas Series, dict with 'x' and 'y', or dict with 'dates' and 'rsi'
            row: Row number for the subplot
            **trace_kwargs: Additional trace configuration options
        """
        try:
            # Handle different data formats
            if hasattr(data, 'index') and hasattr(data, 'values'):
                # Pandas Series-like data
                x_data = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in data.index]
                y_data = data.values.tolist()
            elif isinstance(data, dict):
                if 'x' in data and 'y' in data:
                    # Dictionary with x/y data
                    x_data = data['x']
                    y_data = data['y']
                elif 'dates' in data and 'rsi' in data:
                    # Dictionary with dates/rsi data
                    x_data = data['dates']
                    y_data = data['rsi']
                else:
                    raise ValueError("RSI data dict must contain either 'x'/'y' or 'dates'/'rsi' keys")
            else:
                raise ValueError("RSI data must be pandas Series or dict with appropriate keys")
            
            # Default trace configuration for RSI line
            default_config = {
                'name': 'RSI',
                'line': dict(color='purple', width=2),
                'hovertemplate': '<b>RSI</b><br>Date: %{x}<br>RSI: %{y:.2f}<extra></extra>'
            }
            
            # Merge with user-provided kwargs
            trace_config = {**default_config, **trace_kwargs}
            
            # Add RSI line chart
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines',
                    **trace_config
                ),
                row=row,
                col=1
            )
            
            # Add overbought level (70)
            fig.add_hline(
                y=70,
                line=dict(color='red', width=1, dash='dash'),
                annotation_text='Overbought (70)',
                annotation_position='right',
                row=row,
                col=1
            )
            
            # Add oversold level (30)
            fig.add_hline(
                y=30,
                line=dict(color='green', width=1, dash='dash'),
                annotation_text='Oversold (30)',
                annotation_position='right',
                row=row,
                col=1
            )
            
            # Set y-axis range to show full RSI scale (0-100)
            fig.update_yaxes(range=[0, 100], row=row, col=1)
            
        except Exception as e:
            print(f"Error adding RSI data: {str(e)}")
            # Add empty trace to maintain subplot structure
            fig.add_trace(
                go.Scatter(
                    x=[],
                    y=[],
                    mode='lines',
                    name='RSI (Error)',
                    line=dict(color='red', width=1)
                ),
                row=row,
                col=1
            )
    
    def _add_macd_data(self, fig: go.Figure, data: Any, row: int, **trace_kwargs) -> None:
        """
        Add MACD line and histogram data to subplot.
        
        Args:
            fig: Plotly figure object
            data: MACD data - can be dict with 'macd', 'signal', 'histogram' and 'dates' keys,
                  or dict with 'x' and separate 'macd_line', 'signal_line', 'histogram' keys
            row: Row number for the subplot
            **trace_kwargs: Additional trace configuration options
        """
        try:
            # Handle different data formats
            if isinstance(data, dict):
                if 'dates' in data and 'macd' in data and 'signal' in data and 'histogram' in data:
                    # Dictionary with dates and MACD components
                    x_data = data['dates']
                    macd_line = data['macd']
                    signal_line = data['signal']
                    histogram = data['histogram']
                elif 'x' in data and 'macd_line' in data and 'signal_line' in data and 'histogram' in data:
                    # Dictionary with x and MACD components
                    x_data = data['x']
                    macd_line = data['macd_line']
                    signal_line = data['signal_line']
                    histogram = data['histogram']
                else:
                    raise ValueError("MACD data dict must contain either 'dates'/'macd'/'signal'/'histogram' or 'x'/'macd_line'/'signal_line'/'histogram' keys")
            else:
                raise ValueError("MACD data must be dict with appropriate keys")
            
            # Extract trace configuration options
            macd_config = trace_kwargs.get('macd_config', {})
            signal_config = trace_kwargs.get('signal_config', {})
            histogram_config = trace_kwargs.get('histogram_config', {})
            
            # Default configurations for MACD components
            default_macd_config = {
                'name': 'MACD',
                'line': dict(color='blue', width=2),
                'hovertemplate': '<b>MACD</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>'
            }
            
            default_signal_config = {
                'name': 'Signal',
                'line': dict(color='red', width=2),
                'hovertemplate': '<b>Signal</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>'
            }
            
            default_histogram_config = {
                'name': 'Histogram',
                'marker_color': 'rgba(128, 128, 128, 0.6)',
                'hovertemplate': '<b>Histogram</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>'
            }
            
            # Merge with user-provided configs
            macd_trace_config = {**default_macd_config, **macd_config}
            signal_trace_config = {**default_signal_config, **signal_config}
            histogram_trace_config = {**default_histogram_config, **histogram_config}
            
            # Add MACD line
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=macd_line,
                    mode='lines',
                    **macd_trace_config
                ),
                row=row,
                col=1
            )
            
            # Add Signal line
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=signal_line,
                    mode='lines',
                    **signal_trace_config
                ),
                row=row,
                col=1
            )
            
            # Add Histogram bars
            fig.add_trace(
                go.Bar(
                    x=x_data,
                    y=histogram,
                    **histogram_trace_config
                ),
                row=row,
                col=1
            )
            
            # Add zero line for reference
            fig.add_hline(
                y=0,
                line=dict(color='black', width=1, dash='dot'),
                row=row,
                col=1
            )
            
        except Exception as e:
            print(f"Error adding MACD data: {str(e)}")
            # Add empty traces to maintain subplot structure
            fig.add_trace(
                go.Scatter(
                    x=[],
                    y=[],
                    mode='lines',
                    name='MACD (Error)',
                    line=dict(color='red', width=1)
                ),
                row=row,
                col=1
            )
    
    def _add_time_selector_data(self, fig: go.Figure, data: Any, row: int, **trace_kwargs) -> None:
        """
        Add time selector data to subplot.
        
        Args:
            fig: Plotly figure object
            data: Time selector data - can be pandas Series, dict with 'x' and 'y', or dict with 'dates' and 'values'
            row: Row number for the subplot
            **trace_kwargs: Additional trace configuration options
        """
        try:
            # Handle different data formats
            if hasattr(data, 'index') and hasattr(data, 'values'):
                # Pandas Series-like data
                x_data = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in data.index]
                y_data = data.values.tolist()
            elif isinstance(data, dict):
                if 'x' in data and 'y' in data:
                    # Dictionary with x/y data
                    x_data = data['x']
                    y_data = data['y']
                elif 'dates' in data and 'values' in data:
                    # Dictionary with dates/values data
                    x_data = data['dates']
                    y_data = data['values']
                else:
                    raise ValueError("Time selector data dict must contain either 'x'/'y' or 'dates'/'values' keys")
            else:
                raise ValueError("Time selector data must be pandas Series or dict with appropriate keys")
            
            # Default trace configuration for time selector
            default_config = {
                'name': 'Time Selector',
                'line': dict(color='rgba(128, 128, 128, 0.8)', width=1),
                'fill': 'tonexty',
                'fillcolor': 'rgba(128, 128, 128, 0.3)',
                'hovertemplate': '<b>Time Selector</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>',
                'showlegend': False  # Time selector typically doesn't need legend
            }
            
            # Merge with user-provided kwargs
            trace_config = {**default_config, **trace_kwargs}
            
            # Add time selector area chart
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines',
                    **trace_config
                ),
                row=row,
                col=1
            )
            
            # Add baseline at zero for fill reference
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=[0] * len(x_data),
                    mode='lines',
                    line=dict(color='rgba(0,0,0,0)'),  # Invisible line
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=row,
                col=1
            )
            
        except Exception as e:
            print(f"Error adding time selector data: {str(e)}")
            # Add empty trace to maintain subplot structure
            fig.add_trace(
                go.Scatter(
                    x=[],
                    y=[],
                    mode='lines',
                    name='Time Selector (Error)',
                    line=dict(color='red', width=1)
                ),
                row=row,
                col=1
            )
    
    def _add_generic_subplot_data(self, fig: go.Figure, subplot_name: str, data: Any, 
                                 row: int, **trace_kwargs) -> None:
        """
        Generic method for adding data to custom subplot types.
        
        This method provides extensibility for custom subplot types by supporting
        multiple data formats and trace types.
        
        Args:
            fig: Plotly figure object
            subplot_name: Name of the subplot
            data: Data to plot - supports various formats
            row: Row number for the subplot
            **trace_kwargs: Additional trace configuration options
        """
        try:
            config = self.subplot_configs[subplot_name]
            
            # Determine trace type from kwargs or use default
            trace_type = trace_kwargs.pop('trace_type', 'scatter')
            
            # Handle different data formats
            if hasattr(data, 'index') and hasattr(data, 'values'):
                # Pandas Series-like data
                x_data = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in data.index]
                y_data = data.values.tolist()
            elif isinstance(data, dict):
                if 'x' in data and 'y' in data:
                    # Dictionary with x/y data
                    x_data = data['x']
                    y_data = data['y']
                elif 'dates' in data and 'values' in data:
                    # Dictionary with dates/values data
                    x_data = data['dates']
                    y_data = data['values']
                else:
                    raise ValueError(f"Generic subplot data dict must contain either 'x'/'y' or 'dates'/'values' keys")
            else:
                raise ValueError(f"Generic subplot data must be pandas Series or dict with appropriate keys")
            
            # Default trace configuration
            default_config = {
                'name': config.title or subplot_name,
                'hovertemplate': f'<b>{config.title or subplot_name}</b><br>Date: %{{x}}<br>Value: %{{y:.4f}}<extra></extra>'
            }
            
            # Merge with user-provided kwargs
            trace_config = {**default_config, **trace_kwargs}
            
            # Create appropriate trace based on type
            if trace_type.lower() == 'bar':
                fig.add_trace(
                    go.Bar(
                        x=x_data,
                        y=y_data,
                        **trace_config
                    ),
                    row=row,
                    col=1
                )
            elif trace_type.lower() == 'scatter' or trace_type.lower() == 'line':
                # Default line configuration for scatter plots
                if 'mode' not in trace_config:
                    trace_config['mode'] = 'lines'
                if 'line' not in trace_config:
                    trace_config['line'] = dict(width=2)
                    
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        **trace_config
                    ),
                    row=row,
                    col=1
                )
            elif trace_type.lower() == 'candlestick':
                # For candlestick data, expect OHLC format
                if isinstance(data, dict) and all(k in data for k in ['open', 'high', 'low', 'close']):
                    fig.add_trace(
                        go.Candlestick(
                            x=x_data,
                            open=data['open'],
                            high=data['high'],
                            low=data['low'],
                            close=data['close'],
                            **trace_config
                        ),
                        row=row,
                        col=1
                    )
                else:
                    raise ValueError("Candlestick trace type requires data dict with 'open', 'high', 'low', 'close' keys")
            else:
                # Fallback to scatter plot for unknown trace types
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode='lines',
                        **trace_config
                    ),
                    row=row,
                    col=1
                )
                
        except Exception as e:
            print(f"Error adding generic subplot data for '{subplot_name}': {str(e)}")
            # Add empty trace to maintain subplot structure
            fig.add_trace(
                go.Scatter(
                    x=[],
                    y=[],
                    mode='lines',
                    name=f'{subplot_name} (Error)',
                    line=dict(color='red', width=1)
                ),
                row=row,
                col=1
            )
    
    # Convenience methods for adding specific subplot types
    def add_volume_subplot(self, fig: go.Figure, data: Any, **kwargs) -> None:
        """
        Convenience method to add volume subplot data.
        
        Args:
            fig: Plotly figure object created by create_subplot_figure()
            data: Volume data
            **kwargs: Additional trace configuration options
        """
        self.add_subplot_data(fig, 'volume', data, **kwargs)
    
    def add_rsi_subplot(self, fig: go.Figure, data: Any, **kwargs) -> None:
        """
        Convenience method to add RSI subplot data.
        
        Args:
            fig: Plotly figure object created by create_subplot_figure()
            data: RSI data
            **kwargs: Additional trace configuration options
        """
        self.add_subplot_data(fig, 'rsi', data, **kwargs)
    
    def add_macd_subplot(self, fig: go.Figure, data: Any, **kwargs) -> None:
        """
        Convenience method to add MACD subplot data.
        
        Args:
            fig: Plotly figure object created by create_subplot_figure()
            data: MACD data (dict with macd, signal, histogram components)
            **kwargs: Additional trace configuration options
        """
        self.add_subplot_data(fig, 'macd', data, **kwargs)