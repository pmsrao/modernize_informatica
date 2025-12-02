"""Data Comparator - Implements various data comparison methods."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataComparator:
    """Implements data comparison methods for reconciliation."""
    
    def __init__(self):
        """Initialize data comparator."""
        logger.info("DataComparator initialized")
    
    def compare_counts(self,
                     source_table: Dict[str, Any],
                     target_table: Dict[str, Any],
                     **options) -> Dict[str, Any]:
        """Compare row counts between source and target.
        
        Args:
            source_table: Source table information
            target_table: Target table information
            **options: Additional options (filters, etc.)
            
        Returns:
            Comparison results dictionary
        """
        logger.info(f"Comparing counts: {source_table.get('table_name')} vs {target_table.get('table_name')}")
        
        # In a real implementation, this would execute SQL queries:
        # SELECT COUNT(*) FROM source_table WHERE ...
        # SELECT COUNT(*) FROM target_table WHERE ...
        
        # For now, return a structure that can be populated by actual implementations
        source_count = self._get_count(source_table, options.get('source_filter'))
        target_count = self._get_count(target_table, options.get('target_filter'))
        
        match = source_count == target_count
        difference = abs(source_count - target_count)
        percentage_diff = (difference / source_count * 100) if source_count > 0 else 0
        
        return {
            'method': 'count',
            'status': 'match' if match else 'mismatch',
            'source_count': source_count,
            'target_count': target_count,
            'difference': difference,
            'percentage_difference': percentage_diff,
            'match': match,
            'details': {
                'source_table': source_table.get('table_name'),
                'target_table': target_table.get('table_name')
            }
        }
    
    def compare_hash(self,
                    source_table: Dict[str, Any],
                    target_table: Dict[str, Any],
                    **options) -> Dict[str, Any]:
        """Compare hash values of data between source and target.
        
        Args:
            source_table: Source table information
            target_table: Target table information
            **options: Additional options (hash_columns, etc.)
            
        Returns:
            Comparison results dictionary
        """
        logger.info(f"Comparing hash: {source_table.get('table_name')} vs {target_table.get('table_name')}")
        
        # In a real implementation, this would:
        # 1. Generate hash for each row in source
        # 2. Generate hash for each row in target
        # 3. Compare hash sets
        
        hash_columns = options.get('hash_columns', [])
        source_hash = self._get_table_hash(source_table, hash_columns, options.get('source_filter'))
        target_hash = self._get_table_hash(target_table, hash_columns, options.get('target_filter'))
        
        match = source_hash == target_hash
        
        return {
            'method': 'hash',
            'status': 'match' if match else 'mismatch',
            'source_hash': source_hash,
            'target_hash': target_hash,
            'match': match,
            'hash_columns': hash_columns,
            'details': {
                'source_table': source_table.get('table_name'),
                'target_table': target_table.get('table_name')
            }
        }
    
    def compare_with_threshold(self,
                              source_table: Dict[str, Any],
                              target_table: Dict[str, Any],
                              **options) -> Dict[str, Any]:
        """Compare with tolerance threshold.
        
        Args:
            source_table: Source table information
            target_table: Target table information
            **options: Additional options (threshold, aggregate_columns, etc.)
            
        Returns:
            Comparison results dictionary
        """
        logger.info(f"Comparing with threshold: {source_table.get('table_name')} vs {target_table.get('table_name')}")
        
        threshold = options.get('threshold', 0.01)  # Default 1% tolerance
        aggregate_columns = options.get('aggregate_columns', [])
        
        # Compare aggregates with threshold
        source_aggregates = self._get_aggregates(source_table, aggregate_columns, options.get('source_filter'))
        target_aggregates = self._get_aggregates(target_table, aggregate_columns, options.get('target_filter'))
        
        matches = []
        mismatches = []
        
        for col in aggregate_columns:
            source_val = source_aggregates.get(col, 0)
            target_val = target_aggregates.get(col, 0)
            
            if source_val == 0:
                diff_percent = 100 if target_val != 0 else 0
            else:
                diff_percent = abs((source_val - target_val) / source_val) * 100
            
            is_match = diff_percent <= (threshold * 100)
            
            if is_match:
                matches.append({
                    'column': col,
                    'source_value': source_val,
                    'target_value': target_val,
                    'difference_percent': diff_percent
                })
            else:
                mismatches.append({
                    'column': col,
                    'source_value': source_val,
                    'target_value': target_val,
                    'difference_percent': diff_percent,
                    'threshold': threshold * 100
                })
        
        overall_match = len(mismatches) == 0
        
        return {
            'method': 'threshold',
            'status': 'match' if overall_match else 'mismatch',
            'threshold': threshold,
            'matches': matches,
            'mismatches': mismatches,
            'match': overall_match,
            'details': {
                'source_table': source_table.get('table_name'),
                'target_table': target_table.get('table_name'),
                'aggregate_columns': aggregate_columns
            }
        }
    
    def compare_samples(self,
                       source_table: Dict[str, Any],
                       target_table: Dict[str, Any],
                       **options) -> Dict[str, Any]:
        """Compare samples of data between source and target.
        
        Args:
            source_table: Source table information
            target_table: Target table information
            **options: Additional options (sample_size, sample_percent, random_seed, etc.)
            
        Returns:
            Comparison results dictionary
        """
        logger.info(f"Comparing samples: {source_table.get('table_name')} vs {target_table.get('table_name')}")
        
        sample_size = options.get('sample_size', 1000)
        sample_percent = options.get('sample_percent')
        random_seed = options.get('random_seed', 42)
        
        # Get samples
        source_sample = self._get_sample(source_table, sample_size, sample_percent, random_seed, options.get('source_filter'))
        target_sample = self._get_sample(target_table, sample_size, sample_percent, random_seed, options.get('target_filter'))
        
        # Compare samples
        source_sample_hash = self._hash_sample(source_sample)
        target_sample_hash = self._hash_sample(target_sample)
        
        match = source_sample_hash == target_sample_hash
        
        return {
            'method': 'sampling',
            'status': 'match' if match else 'mismatch',
            'sample_size': sample_size,
            'sample_percent': sample_percent,
            'random_seed': random_seed,
            'source_sample_hash': source_sample_hash,
            'target_sample_hash': target_sample_hash,
            'match': match,
            'details': {
                'source_table': source_table.get('table_name'),
                'target_table': target_table.get('table_name'),
                'note': 'Sample-based comparison - full data may differ'
            }
        }
    
    def _get_count(self, table_info: Dict[str, Any], filter_clause: Optional[str] = None) -> int:
        """Get row count for a table.
        
        Args:
            table_info: Table information
            filter_clause: Optional filter clause
            
        Returns:
            Row count
        """
        # Placeholder - in real implementation, execute SQL query
        # This would connect to Informatica or Databricks and run COUNT query
        logger.debug(f"Getting count for {table_info.get('table_name')}")
        return 0  # Placeholder
    
    def _get_table_hash(self, 
                       table_info: Dict[str, Any],
                       hash_columns: List[str],
                       filter_clause: Optional[str] = None) -> str:
        """Get hash value for a table.
        
        Args:
            table_info: Table information
            hash_columns: Columns to include in hash
            filter_clause: Optional filter clause
            
        Returns:
            Hash value
        """
        # Placeholder - in real implementation, generate hash from data
        logger.debug(f"Getting hash for {table_info.get('table_name')}")
        return hashlib.md5(json.dumps(table_info).encode()).hexdigest()  # Placeholder
    
    def _get_aggregates(self,
                       table_info: Dict[str, Any],
                       aggregate_columns: List[str],
                       filter_clause: Optional[str] = None) -> Dict[str, float]:
        """Get aggregate values for columns.
        
        Args:
            table_info: Table information
            aggregate_columns: Columns to aggregate
            filter_clause: Optional filter clause
            
        Returns:
            Dictionary of column -> aggregate value
        """
        # Placeholder - in real implementation, execute aggregate queries
        logger.debug(f"Getting aggregates for {table_info.get('table_name')}")
        return {col: 0.0 for col in aggregate_columns}  # Placeholder
    
    def _get_sample(self,
                   table_info: Dict[str, Any],
                   sample_size: int,
                   sample_percent: Optional[float],
                   random_seed: int,
                   filter_clause: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sample of data from table.
        
        Args:
            table_info: Table information
            sample_size: Number of rows to sample
            sample_percent: Percentage to sample (alternative to sample_size)
            random_seed: Random seed for reproducibility
            filter_clause: Optional filter clause
            
        Returns:
            List of sample rows
        """
        # Placeholder - in real implementation, execute sample query
        logger.debug(f"Getting sample for {table_info.get('table_name')}")
        return []  # Placeholder
    
    def _hash_sample(self, sample: List[Dict[str, Any]]) -> str:
        """Generate hash for a sample.
        
        Args:
            sample: List of sample rows
            
        Returns:
            Hash value
        """
        sample_str = json.dumps(sample, sort_keys=True, default=str)
        return hashlib.md5(sample_str.encode()).hexdigest()

