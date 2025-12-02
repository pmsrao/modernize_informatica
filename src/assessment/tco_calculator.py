"""TCO Calculator - Total Cost of Ownership and ROI Analysis."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger
from src.assessment.profiler import Profiler

logger = get_logger(__name__)


class TCOCalculator:
    """Calculates TCO and ROI for Informatica to Databricks migration."""
    
    # Default cost assumptions (can be overridden)
    DEFAULT_INFORMATICA_COST_PER_YEAR = 500000  # $500K/year for Informatica PowerCenter
    DEFAULT_DATABRICKS_DBU_COST = 0.55  # $0.55 per DBU
    DEFAULT_DATABRICKS_STORAGE_COST_PER_TB = 240  # $240/TB/month
    
    def __init__(self, profiler: Optional[Profiler] = None):
        """Initialize TCO calculator.
        
        Args:
            profiler: Optional Profiler instance for repository metrics
        """
        self.profiler = profiler
        logger.info("TCOCalculator initialized")
    
    def calculate_tco(self,
                     informatica_annual_cost: Optional[float] = None,
                     databricks_config: Optional[Dict[str, Any]] = None,
                     repository_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate Total Cost of Ownership comparison.
        
        Args:
            informatica_annual_cost: Annual Informatica licensing cost
            databricks_config: Databricks configuration (DBU usage, storage, etc.)
            repository_metrics: Repository metrics from profiler
            
        Returns:
            TCO comparison dictionary
        """
        logger.info("Calculating TCO comparison")
        
        # Get Informatica costs
        informatica_cost = informatica_annual_cost or self.DEFAULT_INFORMATICA_COST_PER_YEAR
        
        # Estimate Databricks costs
        if not databricks_config:
            databricks_config = self._estimate_databricks_config(repository_metrics)
        
        databricks_annual_cost = self._calculate_databricks_cost(databricks_config)
        
        # Calculate savings
        annual_savings = informatica_cost - databricks_annual_cost
        savings_percentage = (annual_savings / informatica_cost * 100) if informatica_cost > 0 else 0
        
        # 3-year TCO
        informatica_3yr = informatica_cost * 3
        databricks_3yr = databricks_annual_cost * 3
        savings_3yr = informatica_3yr - databricks_3yr
        
        return {
            'informatica': {
                'annual_cost': informatica_cost,
                '3_year_cost': informatica_3yr,
                'cost_breakdown': {
                    'licensing': informatica_cost * 0.8,  # 80% licensing
                    'infrastructure': informatica_cost * 0.15,  # 15% infrastructure
                    'maintenance': informatica_cost * 0.05  # 5% maintenance
                }
            },
            'databricks': {
                'annual_cost': databricks_annual_cost,
                '3_year_cost': databricks_3yr,
                'cost_breakdown': databricks_config
            },
            'savings': {
                'annual': annual_savings,
                '3_year': savings_3yr,
                'percentage': savings_percentage
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_roi(self,
                     migration_cost: float,
                     annual_savings: float,
                     years: int = 3) -> Dict[str, Any]:
        """Calculate Return on Investment.
        
        Args:
            migration_cost: One-time migration cost
            annual_savings: Annual cost savings
            years: Number of years for ROI calculation
            
        Returns:
            ROI analysis dictionary
        """
        logger.info(f"Calculating ROI: migration_cost={migration_cost}, annual_savings={annual_savings}, years={years}")
        
        total_savings = annual_savings * years
        net_benefit = total_savings - migration_cost
        roi_percentage = (net_benefit / migration_cost * 100) if migration_cost > 0 else 0
        payback_period_months = (migration_cost / annual_savings * 12) if annual_savings > 0 else 0
        
        return {
            'migration_cost': migration_cost,
            'annual_savings': annual_savings,
            'years': years,
            'total_savings': total_savings,
            'net_benefit': net_benefit,
            'roi_percentage': roi_percentage,
            'payback_period_months': payback_period_months,
            'break_even_year': payback_period_months / 12,
            'timestamp': datetime.now().isoformat()
        }
    
    def estimate_runtime_improvement(self,
                                    repository_metrics: Optional[Dict[str, Any]] = None,
                                    current_runtime_hours: Optional[float] = None) -> Dict[str, Any]:
        """Estimate runtime improvements on Databricks.
        
        Args:
            repository_metrics: Repository metrics from profiler
            current_runtime_hours: Current total runtime in hours per day
            
        Returns:
            Runtime improvement estimates
        """
        logger.info("Estimating runtime improvements")
        
        # Estimate based on repository complexity
        if repository_metrics:
            total_mappings = repository_metrics.get('total_mappings', 0)
            total_workflows = repository_metrics.get('total_workflows', 0)
            
            # Rough estimate: Databricks can be 2-5x faster depending on workload
            # More complex workloads benefit more from parallelization
            complexity_factor = min(total_mappings / 100, 5)  # Cap at 5x
            improvement_factor = 2 + (complexity_factor * 0.5)  # 2x to 4.5x improvement
        else:
            improvement_factor = 3.0  # Default 3x improvement
        
        if current_runtime_hours:
            new_runtime_hours = current_runtime_hours / improvement_factor
            time_saved_hours = current_runtime_hours - new_runtime_hours
            time_saved_percentage = (time_saved_hours / current_runtime_hours * 100) if current_runtime_hours > 0 else 0
        else:
            new_runtime_hours = None
            time_saved_hours = None
            time_saved_percentage = None
        
        return {
            'improvement_factor': improvement_factor,
            'current_runtime_hours': current_runtime_hours,
            'estimated_new_runtime_hours': new_runtime_hours,
            'time_saved_hours': time_saved_hours,
            'time_saved_percentage': time_saved_percentage,
            'assumptions': {
                'note': 'Estimates based on typical Databricks performance improvements',
                'factors': [
                    'Parallel processing capabilities',
                    'Optimized Delta Lake storage',
                    'Photon engine acceleration',
                    'Auto-scaling compute'
                ]
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_cost_analysis_report(self,
                                     tco_data: Dict[str, Any],
                                     roi_data: Optional[Dict[str, Any]] = None,
                                     runtime_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive cost analysis report.
        
        Args:
            tco_data: TCO calculation results
            roi_data: Optional ROI calculation results
            runtime_data: Optional runtime improvement data
            
        Returns:
            Comprehensive cost analysis report
        """
        report = {
            'title': 'Total Cost of Ownership and ROI Analysis',
            'timestamp': datetime.now().isoformat(),
            'tco_analysis': tco_data,
            'roi_analysis': roi_data,
            'runtime_analysis': runtime_data,
            'summary': {
                'annual_savings': tco_data.get('savings', {}).get('annual', 0),
                '3_year_savings': tco_data.get('savings', {}).get('3_year', 0),
                'savings_percentage': tco_data.get('savings', {}).get('percentage', 0)
            }
        }
        
        if roi_data:
            report['summary']['roi_percentage'] = roi_data.get('roi_percentage', 0)
            report['summary']['payback_period_months'] = roi_data.get('payback_period_months', 0)
        
        if runtime_data:
            report['summary']['runtime_improvement_factor'] = runtime_data.get('improvement_factor', 1.0)
        
        return report
    
    def _estimate_databricks_config(self, repository_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate Databricks configuration based on repository metrics.
        
        Args:
            repository_metrics: Repository metrics from profiler
            
        Returns:
            Estimated Databricks configuration
        """
        if not repository_metrics:
            # Default estimates
            return {
                'dbu_per_hour': 10,  # 10 DBU/hour average
                'hours_per_day': 8,
                'days_per_month': 22,
                'storage_tb': 10,
                'compute_cluster_type': 'standard'
            }
        
        total_mappings = repository_metrics.get('total_mappings', 0)
        total_workflows = repository_metrics.get('total_workflows', 0)
        
        # Estimate DBU usage based on workload size
        # Rough estimate: 1-2 DBU per mapping per hour
        base_dbu = max(5, total_mappings * 0.1)  # Minimum 5 DBU, 0.1 DBU per mapping
        
        # Estimate storage (rough: 1GB per mapping)
        storage_tb = max(1, total_mappings * 0.001)  # Minimum 1TB
        
        return {
            'dbu_per_hour': base_dbu,
            'hours_per_day': 8,
            'days_per_month': 22,
            'storage_tb': storage_tb,
            'compute_cluster_type': 'standard'
        }
    
    def _calculate_databricks_cost(self, config: Dict[str, Any]) -> float:
        """Calculate Databricks annual cost.
        
        Args:
            config: Databricks configuration (modified in-place to add cost_breakdown)
            
        Returns:
            Annual cost in USD
        """
        dbu_per_hour = config.get('dbu_per_hour', 10)
        hours_per_day = config.get('hours_per_day', 8)
        days_per_month = config.get('days_per_month', 22)
        storage_tb = config.get('storage_tb', 10)
        
        # Compute cost (DBU * hours * days * months * DBU cost)
        monthly_compute = dbu_per_hour * hours_per_day * days_per_month * self.DEFAULT_DATABRICKS_DBU_COST
        annual_compute = monthly_compute * 12
        
        # Storage cost (TB * cost per TB * months)
        monthly_storage = storage_tb * self.DEFAULT_DATABRICKS_STORAGE_COST_PER_TB
        annual_storage = monthly_storage * 12
        
        total_annual = annual_compute + annual_storage
        
        # Store breakdown in config for later use
        config['cost_breakdown'] = {
            'compute': annual_compute,
            'storage': annual_storage,
            'total': total_annual,
            'monthly_breakdown': {
                'compute': monthly_compute,
                'storage': monthly_storage,
                'total': monthly_compute + monthly_storage
            }
        }
        
        return total_annual

