#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to find specific QGIS terrain analysis algorithms across all providers
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_terrain_algorithms():
    """Find terrain analysis algorithms"""
    
    # Set up QGIS Python paths
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        # Add the Python plugins path
        python_path = os.path.join(conda_prefix, 'share', 'qgis', 'python', 'plugins')
        if os.path.exists(python_path) and python_path not in sys.path:
            sys.path.append(python_path)
        
        qgis_python_path = os.path.join(conda_prefix, 'share', 'qgis', 'python')
        if os.path.exists(qgis_python_path) and qgis_python_path not in sys.path:
            sys.path.append(qgis_python_path)
    
    try:
        from qgis.core import QgsApplication
        
        # Initialize QGIS application with prefix path
        qgis_prefix = conda_prefix if conda_prefix else '/usr'
        logger.info(f"Initializing QGIS with prefix path: {qgis_prefix}")
        
        qgs = QgsApplication([], False)
        qgs.setPrefixPath(qgis_prefix, True)
        qgs.initQgis()
        
        # Import and initialize processing
        import processing
        from processing.core.Processing import Processing
        
        # Initialize processing framework
        Processing.initialize()
        
        # Terms to search for
        search_terms = [
            'rough', 'rugge', 'tpi', 'topographic position', 'slope', 'aspect',
            'terrain', 'curvature', 'tri'
        ]
        
        # Get all algorithms
        all_algorithms = {}
        
        # Get providers
        providers = QgsApplication.processingRegistry().providers()
        
        for provider in providers:
            provider_name = provider.name()
            
            algorithms = provider.algorithms()
            
            # Look for terrain algorithms
            for alg in algorithms:
                alg_id = alg.id()
                alg_name = alg.displayName()
                
                # Check if the algorithm matches any of our search terms
                if any(term.lower() in alg_id.lower() or term.lower() in alg_name.lower() for term in search_terms):
                    if provider_name not in all_algorithms:
                        all_algorithms[provider_name] = []
                    
                    all_algorithms[provider_name].append((alg_id, alg_name))
        
        # Print organized results
        logger.info("=== TERRAIN ANALYSIS ALGORITHMS ===")
        for provider_name, algs in all_algorithms.items():
            logger.info(f"\nProvider: {provider_name}")
            for alg_id, alg_name in sorted(algs):
                logger.info(f"  {alg_id} - {alg_name}")
        
        # Clean up
        qgs.exitQgis()
        
    except Exception as e:
        logger.error(f"Error finding algorithms: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    find_terrain_algorithms()
